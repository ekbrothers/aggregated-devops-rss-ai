# src/aggregator/manual_fetcher.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import logging

def fetch_manual_entries(source, current_week_range):
    entries = []
    try:
        response = requests.get(source['url'])
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text()
        entry_date = datetime.now(pytz.UTC)
        
        if current_week_range[0] <= entry_date < current_week_range[1]:
            entry = {
                'title': source.get('title', 'No Title'),
                'link': source['url'],
                'content': content,
                'published_parsed': entry_date,
                'provider_name': source.get('provider_name', 'Unknown Platform')
            }
            entries.append(entry)
            logging.info(f"Added manual entry: {entry['title']} from {source['url']}")
    except requests.RequestException as e:
        logging.error(f"Failed to fetch manual source: {source['url']} - {str(e)}")
    return entries
