#!/usr/bin/env python3
"""
Debug script to test the scraper function and see what's happening
"""
import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import scrape_songs

def debug_scraper():
    test_date = datetime.date(2025, 6, 10)
    print(f"Testing scraper for date: {test_date}")
    
    # Get the URL that would be generated
    url = f'https://www.officialcharts.com/charts/singles-chart/{test_date.strftime("%Y%m%d")}/7501/'
    print(f"URL: {url}")
    
    # Test the scraper
    songs = scrape_songs(test_date)
    print(f"Number of songs returned: {len(songs)}")
    
    if songs:
        print("\nFirst few songs:")
        for i, song in enumerate(songs[:5]):
            print(f"{i+1}. {song}")
    else:
        print("No songs returned - let's test with a known date")
        # Try a date we know should have chart data (e.g., recent past)
        past_date = datetime.date(2024, 6, 10)
        print(f"\nTrying with past date: {past_date}")
        past_url = f'https://www.officialcharts.com/charts/singles-chart/{past_date.strftime("%Y%m%d")}/7501/'
        print(f"Past URL: {past_url}")
        
        past_songs = scrape_songs(past_date)
        print(f"Number of songs from past date: {len(past_songs)}")
        
        if past_songs:
            print("\nFirst few songs from past date:")
            for i, song in enumerate(past_songs[:5]):
                print(f"{i+1}. {song}")

if __name__ == "__main__":
    debug_scraper()
