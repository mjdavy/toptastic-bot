#!/usr/bin/env python3
import datetime
import logging
import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_playlist_from_db, add_playlist_to_db, create_tables_if_needed
from src.scraper import scrape_songs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("syncdb.log", mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fetch_and_store_songs(date):
    """
    Get songs for a given date. If they don't exist in the database, scrape them from the web.
    
    Args:
        date: datetime.date object representing the date to fetch
    """
    logger.info(f'Getting songs for date {date}.')

    # Convert the date to the desired format (yyyymmdd)
    date_str = date.strftime("%Y%m%d")
    logger.info(f'Converted date {date} to {date_str}.')

    # Check if the playlist is already in the database
    playlist = get_playlist_from_db(date_str)
    if playlist:
        logger.info(f'Playlist for date {date} containing {len(playlist)} songs fetched from the db.')
        return
    
    logger.info(f'Playlist for date {date} not found in the db. Performing web scrape.')
    songs = scrape_songs(date)
    logger.info(f'Playlist for date {date} scraped from web returned {len(songs)} songs.')

    # Add the playlist to the database if we have enough songs
    if len(songs) >= 40:
        add_playlist_to_db(date_str, songs)
    else:
        logger.warning(f'Not enough songs ({len(songs)}) found for {date_str}. Skipping DB update.')

def main():
    """Main function to update the database with chart data."""
    parser = argparse.ArgumentParser(description='Update the song database with chart data.')
    parser.add_argument('--mode', choices=['latest', 'historical'], default='latest',
                        help='Mode to run in: latest (just the most recent chart) or historical (all historical charts)')
    args = parser.parse_args()
    
    # Ensure database tables exist
    create_tables_if_needed()
    
    # Get today's date
    today = datetime.date.today()

    # Find the most recent Friday
    if today.weekday() == 4:  # Friday
        # Today is Friday, use today
        days_since_last_friday = 0
    else:
        # Find the most recent Friday
        days_since_last_friday = (today.weekday() - 4) % 7

    current_date = today - datetime.timedelta(days=days_since_last_friday)
    
    if args.mode == 'latest':
        # Just process the most recent Friday
        logger.info(f'Updating chart data for the most recent Friday: {current_date}')
        try:
            fetch_and_store_songs(current_date)
        except Exception as e:
            logger.error(f"Error updating chart data for {current_date}: {e}")
    else:
        # Process all historical charts
        logger.info('Updating historical chart data')
        
        # Find the first Friday of the year 2000
        start_year = 2000
        year_start = datetime.date(start_year, 1, 1)
        first_friday = year_start + datetime.timedelta(days=(4 - year_start.weekday() + 7) % 7)
        
        # Iterate over all Fridays from the most recent to the first of 2000
        while current_date >= first_friday:
            logger.info(f'Processing chart data for {current_date}')
            try:
                fetch_and_store_songs(current_date)
            except Exception as e:
                logger.error(f"Error processing chart data for {current_date}: {e}")
                
            # Move to the previous Friday
            current_date -= datetime.timedelta(days=7)

if __name__ == "__main__":
    main()