#!/usr/bin/env python3
"""
Debug script to examine the webpage content
"""
import requests
from bs4 import BeautifulSoup
import datetime

def debug_webpage():
    # Test with a known date
    test_date = datetime.date(2024, 6, 10)
    url = f'https://www.officialcharts.com/charts/singles-chart/{test_date.strftime("%Y%m%d")}/7501/'
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for chart rows
            chart_rows = soup.find_all('tr', class_='chart-row')
            print(f"Found {len(chart_rows)} chart rows with class 'chart-row'")
            
            # Check for other possible chart structures
            all_trs = soup.find_all('tr')
            print(f"Found {len(all_trs)} total tr elements")
            
            # Look for any chart-related classes
            chart_elements = soup.find_all(attrs={'class': lambda x: x and 'chart' in ' '.join(x) if isinstance(x, list) else 'chart' in x if x else False})
            print(f"Found {len(chart_elements)} elements with 'chart' in class name")
            
            # Print some of the HTML to see the structure
            print("\nFirst 2000 characters of HTML:")
            print(response.text[:2000])
            print("...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_webpage()
