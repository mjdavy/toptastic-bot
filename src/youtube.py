import logging
import os
import json
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from pathlib import Path

from src.database import get_db_connection
from src.video_selector import build_candidates_from_api, select_best_video

logger = logging.getLogger(__name__)

# Get API keys from environment variable
def get_api_keys():
    api_keys = []
    
    if 'YOUTUBE_API_KEYS' in os.environ:
        api_keys = os.environ['YOUTUBE_API_KEYS'].split(',')
        logger.info(f"Loaded {len(api_keys)} API key(s) from environment variable")
    else:
        logger.error("No YOUTUBE_API_KEYS environment variable found")
        raise ValueError("YOUTUBE_API_KEYS environment variable is required")
    
    return api_keys

# Initialize with the first API key
current_key_index = 0
api_keys = []

# Function to get the YouTube Data API service with the current API key
def get_youtube_service():
    global current_key_index, api_keys
    
    # Load API keys if not already loaded
    if not api_keys:
        api_keys = get_api_keys()
    
    if not api_keys:
        logger.error("No YouTube API keys available")
        raise ValueError("No YouTube API keys available")
    
    api_key = api_keys[current_key_index]
    youtube_service = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    return youtube_service

def get_best_youtube_video(artist: str, song: str):
    """Return best matching YouTube video metadata for a song using heuristic scoring.

    Returns dict with keys: video_id, title, channel_title, score or None.
    """
    global current_key_index
    query = f"{song} {artist}".strip()
    try:
        logger.info(f'Searching YouTube for candidates: "{query}"')
        youtube = get_youtube_service()
        search_request = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=15,
            type='video'
        )
        search_response = search_request.execute()
        items = search_response.get('items', [])
        if not items:
            logger.info(f'No search results for query: {query}')
            return None

        video_ids = [i['id']['videoId'] for i in items]
        # Fetch details in batches of up to 50 (here at most 15)
        details_request = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,contentDetails,statistics'
        )
        details_response = details_request.execute()
        videos_map = {v['id']: v for v in details_response.get('items', [])}

        candidates = build_candidates_from_api(items, videos_map)
        best = select_best_video(candidates, artist, song)
        if not best:
            return None
        logger.info(f"Selected video {best.video_id} score={best.score:.2f} title='{best.title}' channel='{best.channel_title}' reasons={best.reasons}")
        return {
            'video_id': best.video_id,
            'video_title': best.title,
            'channel_title': best.channel_title,
            'video_confidence': best.score,
        }
    except HttpError as e:
        if e.resp.status == 403:
            current_key_index += 1
            if current_key_index >= len(api_keys):
                logger.error('All API keys exhausted (quota) while searching for video')
                return None
            logger.info(f"Quota exceeded. Switching to API key {current_key_index+1}/{len(api_keys)}")
            return get_best_youtube_video(artist, song)
        logger.error(f"YouTube API HTTP error: {e}")
        return None

def get_scored_candidates(artist: str, song: str, limit: int = 15):
    """Return a list of scored candidate videos (dicts) for manual analysis.

    Each element contains: video_id, title, channel_title, score, reasons (list), view_count, duration_seconds.
    """
    global current_key_index
    query = f"{song} {artist}".strip()
    try:
        youtube = get_youtube_service()
        search_request = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=min(limit, 50),
            type='video'
        )
        sr = search_request.execute()
        items = sr.get('items', [])
        if not items:
            return []
        video_ids = [i['id']['videoId'] for i in items]
        details = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,contentDetails,statistics'
        ).execute()
        vmap = {v['id']: v for v in details.get('items', [])}
        candidates = build_candidates_from_api(items, vmap)
        # Score (select_best_video internally scores; replicate to preserve reasons)
        from src.video_selector import score_candidate
        scored = [score_candidate(c, artist, song) for c in candidates]
        scored.sort(key=lambda c: (c.score, c.view_count), reverse=True)
        out = []
        for c in scored:
            out.append({
                'video_id': c.video_id,
                'title': c.title,
                'channel_title': c.channel_title,
                'score': c.score,
                'reasons': c.reasons,
                'view_count': c.view_count,
                'duration_seconds': c.duration_seconds,
            })
        return out
    except HttpError as e:
        if e.resp.status == 403:
            current_key_index += 1
            if current_key_index >= len(api_keys):
                return []
            return get_scored_candidates(artist, song, limit=limit)
        return []
    except Exception:
        return []
    except Exception as e:
        logger.error(f"Unexpected error selecting video: {e}")
        return None

def update_video_ids():
    """Update video IDs and associated metadata for songs missing them."""
    conn = get_db_connection()
    # Ensure new columns exist (non-destructive tries)
    try:
        conn.execute('ALTER TABLE songs ADD COLUMN video_title TEXT')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE songs ADD COLUMN channel_title TEXT')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE songs ADD COLUMN video_confidence REAL')
    except Exception:
        pass

    songs = conn.execute('SELECT * FROM songs WHERE video_id IS NULL OR video_id = ""').fetchall()
    logger.info(f'Updating video metadata for {len(songs)} songs')

    update_count = 0
    for row in songs:
        song = dict(row)
        try:
            meta = get_best_youtube_video(song['artist'], song['song_name'])
            if meta and meta.get('video_id'):
                conn.execute(
                    'UPDATE songs SET video_id = ?, video_title = ?, channel_title = ?, video_confidence = ? WHERE id = ?',
                    (meta['video_id'], meta.get('video_title'), meta.get('channel_title'), meta.get('video_confidence'), song['id'])
                )
                conn.commit()
                update_count += 1
                logger.info(f"Updated video metadata for '{song['song_name']}' by '{song['artist']}' -> {meta['video_id']}")
            else:
                logger.info(f"No suitable video found for '{song['song_name']}' by '{song['artist']}'")
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', ('', song['id']))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating video metadata for '{song['song_name']}' by '{song['artist']}': {e}")

    logger.info(f'{update_count} videos updated successfully')
    remaining = conn.execute('SELECT count(*) FROM songs WHERE video_id IS NULL').fetchone()[0]
    logger.info(f'{remaining} songs without video IDs remaining')
    conn.close()