#!/usr/bin/env python
"""Analyze top N chart songs for potentially better YouTube video matches.

Usage:
  python scripts/analyze_top_videos.py --date 20250926 --limit 10 [--apply]
If --date omitted, uses latest playlist date in DB.

Requires YOUTUBE_API_KEYS in environment.
"""
import argparse
import os
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Ensure project root on sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.youtube import get_scored_candidates, get_best_youtube_video
from src.database import get_db_connection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def get_latest_date(conn: sqlite3.Connection) -> Optional[str]:
    row = conn.execute('SELECT date FROM playlists ORDER BY date DESC LIMIT 1').fetchone()
    return row[0] if row else None

def load_top_songs(conn: sqlite3.Connection, date: str, limit: int):
    rows = conn.execute('''
        SELECT s.id, s.song_name, s.artist, s.video_id, s.video_title, s.channel_title, s.video_confidence, ps.position
        FROM playlists p
        JOIN playlist_songs ps ON p.id = ps.playlist_id
        JOIN songs s ON s.id = ps.song_id
        WHERE p.date = ?
        ORDER BY ps.position ASC
        LIMIT ?
    ''', (date, limit)).fetchall()
    return [dict(r) for r in rows]


def analyze_song(song):
    artist = song['artist']
    title = song['song_name']
    candidates = get_scored_candidates(artist, title, limit=15)
    current_id = song.get('video_id') or ''
    best = candidates[0] if candidates else None
    improved = False
    if best and best['video_id'] and best['video_id'] != current_id:
        # Consider improvement only if score delta significant (>5) or current empty
        old_score = song.get('video_confidence') or 0.0
        if (best['score'] - old_score) > 5 or not current_id:
            improved = True
    return {
        'song': song,
        'candidates': candidates,
        'best': best,
        'improved': improved
    }


def maybe_apply(conn, analysis_result):
    if not analysis_result['improved']:
        return False
    song = analysis_result['song']
    best = analysis_result['best']
    conn.execute('''UPDATE songs SET video_id = ?, video_title = ?, channel_title = ?, video_confidence = ? WHERE id = ?''',
                 (best['video_id'], best['title'], best['channel_title'], best['score'], song['id']))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='Chart date yyyymmdd; defaults to latest in DB')
    parser.add_argument('--limit', type=int, default=10, help='Number of top songs to analyze (default 10)')
    parser.add_argument('--apply', action='store_true', help='Apply better matches to DB')
    parser.add_argument('--min-score', type=float, default=0.0, help='Only consider replacements if best score >= this')
    args = parser.parse_args()

    if 'YOUTUBE_API_KEYS' not in os.environ:
        parser.error('YOUTUBE_API_KEYS environment variable required')

    conn = get_db_connection()
    date = args.date or get_latest_date(conn)
    if not date:
        parser.error('No playlists found in database and no --date supplied')

    songs = load_top_songs(conn, date, args.limit)
    if not songs:
        parser.error(f'No songs found for date {date}')

    logger.info(f'Analyzing top {len(songs)} songs for chart date {date}')
    applied = 0
    for song in songs:
        analysis = analyze_song(song)
        best = analysis['best']
        print('\n' + '='*80)
        print(f"{song['position']:02d}. {song['artist']} - {song['song_name']}")
        print(f"Current: {song.get('video_id') or '(none)'} | score={song.get('video_confidence')} title={song.get('video_title')}")
        if not best:
            print('No candidates found.')
            continue
        print(f"Best:    {best['video_id']} | score={best['score']:.2f} {best['title']} [{best['channel_title']}]")
        if analysis['improved'] and best['score'] >= args.min_score:
            print('=> Improvement candidate found.')
            if args.apply:
                if maybe_apply(conn, analysis):
                    conn.commit()
                    applied += 1
                    print('Applied update.')
        # Show top 5 candidates
        for i, c in enumerate(analysis['candidates'][:5], start=1):
            marker = '*' if c['video_id'] == (best['video_id'] if best else None) else ' '
            print(f"  {marker}{i}. {c['score']:.2f} {c['video_id']} | {c['title']} | {c['channel_title']} | reasons={','.join(c.get('reasons') or [])}")

    if args.apply:
        print(f"\nApplied {applied} updates.")
    conn.close()

if __name__ == '__main__':
    main()
