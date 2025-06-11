import pytest
import logging
from datetime import date
from src.scraper_new import scrape_songs_new

# Set up logging for the test
logging.basicConfig(level=logging.INFO)

def test_scrape_songs_new_june_10_2025():
    """
    Test the scrape_songs_new function using June 10, 2025 as the date
    against the real Official Charts website.
    """
    # Test date - June 10, 2025
    test_date = "20250610"  # Format expected by the function
    
    # Call the scraper function
    songs = scrape_songs_new(test_date)
    
    # Basic assertions
    assert isinstance(songs, list), "Function should return a list"
    
    if len(songs) > 0:
        # Test the structure of the first song
        first_song = songs[0]
        
        # Check that all required fields are present
        required_fields = ['song_name', 'artist', 'lw', 'peak', 'weeks', 'is_new', 'is_reentry', 'video_id']
        for field in required_fields:
            assert field in first_song, f"Song should contain field: {field}"
        
        # Check data types
        assert isinstance(first_song['song_name'], str), "Song name should be a string"
        assert isinstance(first_song['artist'], str), "Artist should be a string"
        assert isinstance(first_song['lw'], int), "Last week position should be an integer"
        assert isinstance(first_song['peak'], int), "Peak position should be an integer"
        assert isinstance(first_song['weeks'], int), "Weeks on chart should be an integer"
        assert isinstance(first_song['is_new'], bool), "is_new should be a boolean"
        assert isinstance(first_song['is_reentry'], bool), "is_reentry should be a boolean"
        assert isinstance(first_song['video_id'], str), "video_id should be a string"
        
        # Check that song name and artist are not empty
        assert first_song['song_name'].strip() != "", "Song name should not be empty"
        assert first_song['artist'].strip() != "", "Artist should not be empty"
        
        # Check that peak and weeks are positive
        assert first_song['peak'] > 0, "Peak position should be positive"
        assert first_song['weeks'] > 0, "Weeks on chart should be positive"
        
        print(f"Successfully scraped {len(songs)} songs")
        print(f"First song: {first_song['song_name']} by {first_song['artist']}")
        
    else:
        print("No songs found - this might be expected if the chart for this date doesn't exist yet")

def test_scrape_songs_new_known_date():
    """
    Test with a known past date that should have chart data.
    Using a date from 2024 to ensure data exists.
    """
    # Use a known date from 2024 (June 10, 2024)
    test_date = "20240610"
    
    songs = scrape_songs_new(test_date)
    
    assert isinstance(songs, list), "Function should return a list"
    assert len(songs) > 0, f"Should find songs for date {test_date}"
    
    print(f"Found {len(songs)} songs for {test_date}")
    if songs:
        print(f"Sample song: {songs[0]['song_name']} by {songs[0]['artist']}")

if __name__ == "__main__":
    # Run the tests directly
    test_scrape_songs_new_june_10_2025()
    test_scrape_songs_new_known_date()
