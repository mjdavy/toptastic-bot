#!/usr/bin/env python3
"""Export CSV snapshots from songs.db for publication.

Outputs:
  public/latest_playlist.csv  (latest Friday playlist with joined fields)
  public/songs.csv            (unique songs master list)

The script assumes it is run from repo root or with CWD containing songs.db.
"""

import csv
import datetime
import logging
import os
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path('songs.db')
PUBLIC_DIR = Path('public')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def latest_friday_date(conn):
    cur = conn.execute("SELECT date FROM playlists ORDER BY date DESC LIMIT 1")
    row = cur.fetchone()
    return row['date'] if row else None


def export_latest_playlist(conn, date_str: str):
    query = """
    SELECT 
      p.date AS chart_date,
      ps.position,
      s.song_name,
      s.artist,
      ps.lw,
      ps.peak,
      ps.weeks,
      ps.is_new,
      ps.is_reentry,
      s.video_id
    FROM playlists p
    JOIN playlist_songs ps ON p.id = ps.playlist_id
    JOIN songs s ON ps.song_id = s.id
    WHERE p.date = ?
    ORDER BY ps.position ASC
    """
    rows = conn.execute(query, (date_str,)).fetchall()
    out_path = PUBLIC_DIR / 'latest_playlist.csv'
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'chart_date','position','song_name','artist','lw','peak','weeks','is_new','is_reentry','video_id'
        ])
        for r in rows:
            writer.writerow([
                r['chart_date'], r['position'], r['song_name'], r['artist'], r['lw'], r['peak'], r['weeks'],
                int(r['is_new']), int(r['is_reentry']), r['video_id'] or ''
            ])
    logger.info(f"Exported latest playlist ({date_str}) to {out_path}")


def export_songs_master(conn):
    query = "SELECT id, song_name, artist, COALESCE(video_id,'') AS video_id FROM songs ORDER BY artist, song_name"
    rows = conn.execute(query).fetchall()
    out_path = PUBLIC_DIR / 'songs.csv'
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id','song_name','artist','video_id'])
        for r in rows:
            writer.writerow([r['id'], r['song_name'], r['artist'], r['video_id']])
    logger.info(f"Exported songs master ({len(rows)} rows) to {out_path}")


def main():
    if not DB_PATH.exists():
        raise SystemExit("songs.db not found; run update scripts first")
    PUBLIC_DIR.mkdir(exist_ok=True)
    conn = get_connection()
    try:
        date_str = latest_friday_date(conn)
        if not date_str:
            logger.warning("No playlists found; skipping playlist export")
        else:
            export_latest_playlist(conn, date_str)
        export_songs_master(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
