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
    date_str = date.strftime("%Y%m%d")
    url = f'https://www.officialcharts.com/charts/singles-chart/{date_str}/7501/'
    logger.info(f"Scraping chart data from: {url}")
    
    # Make a request to the website
    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve chart data. Status code: {response.status_code}")
        return []

    # Use BeautifulSoup to parse the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the div tags with class 'description block'
    divs = soup.find_all('div', class_='description block')
    
    # Create a list to store the song data
    songs = []
    
    # Extract song information from each chart entry
    for position, div in enumerate(divs, 1):
        try:
            song_name_tag = div.find('a', class_='chart-name font-bold inline-block')
            if song_name_tag is None:
                logger.error(f'Unable to find song name tag for div at position {position}')
                continue

            song_name_elements = song_name_tag.find_all('span')
            if len(song_name_elements) == 0:
                logger.error(f'Unable to find song name elements for div at position {position}')
                continue

            re_new = song_name_elements[0].get_text(strip=True).upper() if len(song_name_elements) > 1 else ''
            song_name = song_name_elements[-1].get_text(strip=True)

            artist_tag = div.find('a', class_='chart-artist text-lg inline-block')
            if artist_tag is None:
                logger.error(f'Unable to find artist tag for div at position {position}')
                continue
            artist = artist_tag.get_text(strip=True)

            lw_tag = div.find('li', class_='movement px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
            if lw_tag is None:
                logger.error(f'Unable to find lw tag for div at position {position}')
                continue
            lw = lw_tag.get_text(strip=True).split(':')[1].replace(',', '').strip()

            peak_tag = div.find('li', class_='peak px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
            if peak_tag is None:
                logger.error(f'Unable to find peak tag for div at position {position}')
                continue
            peak = peak_tag.get_text(strip=True).split(':')[1].replace(',', '').strip()

            weeks_tag = div.find('li', class_='weeks px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
            if weeks_tag is None:
                logger.error(f'Unable to find weeks tag for div at position {position}')
                continue
            weeks = weeks_tag.get_text(strip=True).split(':')[1].strip()

            # Determine if the song is new or a reentry
            is_new = re_new.lower() == 'new' or lw.lower() == 'new'
            is_reentry = re_new.lower() == 're' or lw.lower() == 're'

            # If the song is new or a reentry, set lw to 0
            if is_new or is_reentry:
                lw_int = 0
            else:
                try:
                    lw_int = int(lw) if lw else 0
                except ValueError:
                    lw_int = 0

            try:
                peak_int = int(peak) if peak else position
            except ValueError:
                peak_int = position

            try:
                weeks_int = int(weeks) if weeks else 1
            except ValueError:
                weeks_int = 1

            # Create song dictionary
            song = {
                'position': position,
                'song_name': song_name,
                'artist': artist,
                'lw': lw_int,
                'peak': peak_int,
                'weeks': weeks_int,
                'is_new': is_new,
                'is_reentry': is_reentry,
                'video_id': None  # Will be populated later by the YouTube module
            }
            
            songs.append(song)
            
        except Exception as e:
            logger.error(f"Error parsing chart entry at position {position}: {e}")
    
    logger.info(f"Scraped {len(songs)} songs from chart for date {date}")
    return songs