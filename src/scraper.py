import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def scrape_songs(date):
    """
    Scrape songs from the Official Charts website for a specific date.
    
    Args:
        date: datetime.date object representing the date to scrape
        
    Returns:
        list: List of song dictionaries with chart information
    """
    # Format the URL for the Official Charts website
    url = f'https://www.officialcharts.com/charts/singles-chart/{date.strftime("%Y%m%d")}/7501/'
    logger.info(f"Scraping chart data from: {url}")
    
    # Make a request to the website
    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve chart data. Status code: {response.status_code}")
        return []

    # Use BeautifulSoup to parse the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the chart entries
    chart_rows = soup.find_all('tr', class_='chart-row')
    
    # Create a list to store the song data
    songs = []
    
    # Extract song information from each chart entry
    for row in chart_rows:
        try:
            # Get the position
            position_elem = row.find('span', class_='position')
            if not position_elem:
                continue
            position = int(position_elem.text.strip())
            
            # Get the song name
            title_elem = row.find('div', class_='title')
            if not title_elem:
                continue
            song_name = title_elem.text.strip()
            
            # Get the artist
            artist_elem = row.find('div', class_='artist')
            if not artist_elem:
                continue
            artist = artist_elem.text.strip()
            
            # Get the chart statistics (Last Week, Peak, Weeks on Chart)
            stats_elems = row.find_all('td', class_='chart-position')
            
            # Process last week position
            lw_text = stats_elems[0].text.strip() if len(stats_elems) > 0 else ''
            
            is_new = False
            is_reentry = False
            
            if lw_text.lower() == 'new':
                lw = 0
                is_new = True
            elif lw_text.lower() == 're':
                lw = 0
                is_reentry = True
            else:
                try:
                    lw = int(lw_text) if lw_text else 0
                except ValueError:
                    lw = 0
            
            # Process peak position
            peak_text = stats_elems[1].text.strip() if len(stats_elems) > 1 else ''
            try:
                peak = int(peak_text) if peak_text else position
            except ValueError:
                peak = position
            
            # Process weeks on chart
            weeks_text = stats_elems[2].text.strip() if len(stats_elems) > 2 else ''
            try:
                weeks = int(weeks_text) if weeks_text else 1
            except ValueError:
                weeks = 1
            
            # Create song dictionary
            song = {
                'position': position,
                'song_name': song_name,
                'artist': artist,
                'lw': lw,
                'peak': peak,
                'weeks': weeks,
                'is_new': is_new,
                'is_reentry': is_reentry,
                'video_id': None  # Will be populated later by the YouTube module
            }
            
            songs.append(song)
            
        except Exception as e:
            logger.error(f"Error parsing chart entry: {e}")
    
    logger.info(f"Scraped {len(songs)} songs from chart for date {date}")
    return songs