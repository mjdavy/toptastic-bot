import logging
import os
import json
import googleapiclient.discovery
from pathlib import Path

from src.database import get_db_connection

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

def get_youtube_video_id(query):
    """
    Search YouTube for a video matching the query and return its ID.
    
    Args:
        query: Search query string (typically artist + song name)
        
    Returns:
        str: YouTube video ID or None if not found
    """
    global current_key_index
    
    try:
        logger.info(f'Getting video ID for "{query}" from YouTube')
        youtube = get_youtube_service()
        request = youtube.search().list(
            q=query,
            part='id',
            maxResults=1,
            type='video'
        )
        response = request.execute()

        items = response.get('items', [])
        if items:
            video_id = items[0]['id']['videoId']
            logger.info(f'Found video ID: {video_id}')
            return video_id
        else:
            logger.info(f'No video found for query: "{query}"')
            return None
        
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 403:
            # Quota exceeded error, switch to the next API key
            current_key_index += 1
            if current_key_index >= len(api_keys):
                # All quotas are used up
                logger.error("All API keys have exceeded their quotas")
                return None
            else:
                # Retry with the next API key
                logger.info(f"Switching to API key {current_key_index+1}/{len(api_keys)}")
                return get_youtube_video_id(query)
        else:
            # Other HTTP error
            logger.error(f"HTTP error occurred: {e}")
            return None
    except Exception as e:
        logger.error(f"Error getting YouTube video ID: {e}")
        return None

def update_video_ids():
    """
    Update video IDs for songs that don't have them.
    """
    conn = get_db_connection()
    songs = conn.execute('SELECT * FROM songs WHERE video_id IS NULL').fetchall()

    logger.info(f'Updating video IDs for {len(songs)} songs')

    update_count = 0
    for row in songs:
        song = dict(row)
        try: 
            video_id = get_youtube_video_id(f"{song['song_name']} {song['artist']}")
            if video_id:
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', (video_id, song['id']))
                conn.commit()  # commit after each update
                song['video_id'] = video_id
                update_count += 1
                logger.info(f"Updated video ID for '{song['song_name']}' by '{song['artist']}': {video_id}")
            else:
                logger.info(f"No video ID found for '{song['song_name']}' by '{song['artist']}'")
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', ('', song['id']))  # Set video ID to empty string
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating video ID for '{song['song_name']}' by '{song['artist']}': {e}")
            
    logger.info(f'{update_count} video IDs updated successfully')
    remaining = conn.execute('SELECT count(*) FROM songs WHERE video_id IS NULL').fetchone()[0]
    logger.info(f'{remaining} songs without video IDs remaining')
    conn.close()