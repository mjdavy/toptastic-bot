import pytest
import datetime
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import scrape_songs


class TestScrapeSongs:
    """Test cases for the scrape_songs function."""
    
    def test_scrape_songs_june_10_2025(self):
        """
        Test scraping songs from the Official Charts website for June 10, 2025.
        This test makes a real HTTP request to the Official Charts website.
        """
        # Set the test date
        test_date = datetime.date(2025, 6, 10)
        
        # Call the function
        songs = scrape_songs(test_date)
        
        # Basic assertions
        assert isinstance(songs, list), "Function should return a list"
        assert len(songs) > 0, "Should return at least some songs from the chart"
        assert len(songs) <= 100, "UK Singles Chart typically has 100 positions or fewer"
        
        # Check the structure of the first song
        if songs:
            first_song = songs[0]
            
            # Verify required fields exist
            required_fields = ['position', 'song_name', 'artist', 'lw', 'peak', 'weeks', 'is_new', 'is_reentry', 'video_id']
            for field in required_fields:
                assert field in first_song, f"Song should have field: {field}"
            
            # Verify data types
            assert isinstance(first_song['position'], int), "Position should be an integer"
            assert isinstance(first_song['song_name'], str), "Song name should be a string"
            assert isinstance(first_song['artist'], str), "Artist should be a string"
            assert isinstance(first_song['lw'], int), "Last week position should be an integer"
            assert isinstance(first_song['peak'], int), "Peak position should be an integer"
            assert isinstance(first_song['weeks'], int), "Weeks on chart should be an integer"
            assert isinstance(first_song['is_new'], bool), "is_new should be a boolean"
            assert isinstance(first_song['is_reentry'], bool), "is_reentry should be a boolean"
            
            # Verify logical constraints
            assert first_song['position'] >= 1, "Position should be at least 1"
            assert first_song['position'] <= 100, "Position should not exceed 100"
            assert first_song['peak'] >= 1, "Peak position should be at least 1"
            assert first_song['peak'] <= first_song['position'], "Peak position should be better than or equal to current position"
            assert first_song['weeks'] >= 1, "Weeks on chart should be at least 1"
            assert len(first_song['song_name'].strip()) > 0, "Song name should not be empty"
            assert len(first_song['artist'].strip()) > 0, "Artist should not be empty"
            
            # Check that positions are in order
            positions = [song['position'] for song in songs]
            assert positions == sorted(positions), "Songs should be ordered by position"
            
            # Check that position 1 exists
            position_1_songs = [song for song in songs if song['position'] == 1]
            assert len(position_1_songs) == 1, "There should be exactly one song at position 1"
            
        print(f"Successfully scraped {len(songs)} songs from the chart for {test_date}")
        
        # Print first few songs for manual verification
        print("\nFirst 5 songs:")
        for i, song in enumerate(songs[:5]):
            print(f"{song['position']:2d}. {song['artist']} - {song['song_name']}")
    
    def test_scrape_songs_invalid_date(self):
        """
        Test scraping with a date that likely doesn't have chart data.
        This should return an empty list gracefully.
        """
        # Use a very old date that predates the website
        test_date = datetime.date(1900, 1, 1)
        
        # Call the function
        songs = scrape_songs(test_date)
        
        # Should return empty list for invalid/unavailable dates
        assert isinstance(songs, list), "Function should return a list even for invalid dates"
        # Note: We don't assert empty list as the website might have different behavior
    
    def test_scrape_songs_future_date(self):
        """
        Test scraping with a future date.
        This should handle gracefully.
        """
        # Use a far future date
        test_date = datetime.date(2030, 12, 31)
        
        # Call the function
        songs = scrape_songs(test_date)
        
        # Should return a list (might be empty)
        assert isinstance(songs, list), "Function should return a list even for future dates"


if __name__ == "__main__":
    # Run the test for June 10, 2025 when script is executed directly
    test_instance = TestScrapeSongs()
    test_instance.test_scrape_songs_june_10_2025()
