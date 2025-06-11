import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def scrape_songs_new(date):

    # Make a request to the website
    url = f'https://www.officialcharts.com/charts/singles-chart/{date}/7501/' 
    response = requests.get(url)

    # Use the 'html.parser' to parse the page
    soup = BeautifulSoup(response.text, 'html.parser')

     # Find all the div tags with class 'description block'
    divs = soup.find_all('div', class_='description block')

    # Create a list to store the song data
    songs = []

     # Extract and print the song name, artist, and chart information
    for div in divs:
        song_name_tag = div.find('a', class_='chart-name font-bold inline-block')
        if song_name_tag is None:
            logger.error(f'Unable to find song name tag for div: {div}')
            continue

        song_name_elements = song_name_tag.find_all('span')
        if len(song_name_elements) == 0:
            logger.error(f'Unable to find song name elements for div: {div}')
            continue

        re_new = song_name_elements[0].get_text(strip=True).upper() if len(song_name_elements) > 1 else ''
        song_name = song_name_elements[-1].get_text(strip=True)

        artist_tag = div.find('a', class_='chart-artist text-lg inline-block')
        if artist_tag is None:
            logger.error(f'Unable to find artist tag for div: {div}')
            continue
        artist = artist_tag.get_text(strip=True)

        lw_tag = div.find('li', class_='movement px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if lw_tag is None:
            logger.error(f'Unable to find lw tag for div: {div}')
            continue
        lw = lw_tag.get_text(strip=True).split(':')[1].replace(',', '')

        peak_tag = div.find('li', class_='peak px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if peak_tag is None:
            logger.error(f'Unable to find peak tag for div: {div}')
            continue
        peak = peak_tag.get_text(strip=True).split(':')[1].replace(',', '')

        weeks_tag = div.find('li', class_='weeks px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if weeks_tag is None:
            logger.error(f'Unable to find weeks tag for div: {div}')
            continue
        weeks = weeks_tag.get_text(strip=True).split(':')[1]

        video_id = ''  # This will be populated by a separate process

        # Determine if the song is new or a reentry
        is_new = re_new.lower() == 'new' or lw.lower() == 'new'
        is_reentry = re_new.lower() == 're' or lw.lower() == 're'

         # If the song is new or a reentry, set lw to 0
        if is_new or is_reentry:
            lw = 0

        song = {
            'is_new': bool(is_new), 
            'is_reentry': bool(is_reentry),
            'song_name': song_name,
            'artist': artist,
            'lw': int(lw),
            'peak': int(peak),
            'weeks': int(weeks),
            'video_id': video_id
        }
        
        songs.append(song)

    logger.info(f'Songs for date {date} scraped from web successfully.')
    return songs