import logging
import sqlite3
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect('songs.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables_if_needed():
    """Create the database tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables for songs, playlists, and playlist_songs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_name TEXT NOT NULL,
            artist TEXT NOT NULL,
            video_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER,
            song_id INTEGER,
            position INTEGER,
            lw INTEGER,
            peak INTEGER,
            weeks INTEGER,
            is_new INTEGER,
            is_reentry INTEGER,
            PRIMARY KEY (playlist_id, song_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id),
            FOREIGN KEY (song_id) REFERENCES songs(id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database tables created or verified")

def get_playlist_from_db(date):
    """Retrieve a playlist from the database for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try to find the playlist for the given date
    cursor.execute('''
        SELECT 
            s.id,
            s.song_name, 
            s.artist, 
            s.video_id,
            ps.position, 
            ps.lw, 
            ps.peak, 
            ps.weeks, 
            ps.is_new, 
            ps.is_reentry
        FROM 
            playlists p 
            JOIN playlist_songs ps ON p.id = ps.playlist_id 
            JOIN songs s ON ps.song_id = s.id
        WHERE 
            p.date = ?
        ORDER BY
            ps.position
    ''', (date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        logger.info(f"No playlist found for date {date}")
        return None

    # Convert rows to list of dictionaries
    playlist = []
    for row in rows:
        song = dict(row)
        playlist.append({
            'id': song['id'],
            'position': song['position'],
            'song_name': song['song_name'],
            'artist': song['artist'],
            'lw': song['lw'],
            'peak': song['peak'],
            'weeks': song['weeks'],
            'is_new': bool(song['is_new']), 
            'is_reentry': bool(song['is_reentry']),
            'video_id': song['video_id']
        })
    
    logger.info(f"Retrieved playlist for {date} with {len(playlist)} songs")
    return playlist

def add_playlist_to_db(date, songs):
    """Add a playlist to the database for a specific date."""
    if not songs:
        logger.warning(f"No songs provided for date {date}, skipping database update")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if playlist already exists
        cursor.execute('SELECT id FROM playlists WHERE date = ?', (date,))
        existing_playlist = cursor.fetchone()
        
        if existing_playlist:
            logger.info(f"Playlist for {date} already exists, updating")
            playlist_id = existing_playlist['id']
            # Delete existing playlist songs
            cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = ?', (playlist_id,))
        else:
            # Create new playlist
            cursor.execute('INSERT INTO playlists (date) VALUES (?)', (date,))
            playlist_id = cursor.lastrowid
            logger.info(f"Created new playlist for {date} with ID {playlist_id}")
        
        # Add songs to playlist
        for song in songs:
            # Check if song exists
            cursor.execute(
                'SELECT id FROM songs WHERE song_name = ? AND artist = ?', 
                (song['song_name'], song['artist'])
            )
            existing_song = cursor.fetchone()
            
            if existing_song:
                song_id = existing_song['id']
            else:
                # Create new song
                cursor.execute(
                    'INSERT INTO songs (song_name, artist) VALUES (?, ?)',
                    (song['song_name'], song['artist'])
                )
                song_id = cursor.lastrowid
            
            # Add song to playlist
            cursor.execute('''
                INSERT INTO playlist_songs 
                (playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                playlist_id, 
                song_id,
                song['position'],
                song['lw'],
                song['peak'],
                song['weeks'],
                1 if song['is_new'] else 0,
                1 if song['is_reentry'] else 0
            ))
        
        conn.commit()
        logger.info(f"Successfully added {len(songs)} songs to playlist for {date}")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding playlist for date {date}: {e}")
    
    finally:
        conn.close()

def debug_dump_songs(songs):
    """Log a prettified JSON representation of the songs."""
    if not songs:
        logger.warning("No songs to dump")
        return
        
    try:
        for song in songs:
            logger.debug(f"{song.get('position', 'N/A')} - {song.get('song_name', 'Unknown')} by {song.get('artist', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error dumping songs: {e}")