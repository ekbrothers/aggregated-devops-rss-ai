# src/aggregator/feed_fetcher.py
import feedparser
from datetime import datetime
import pytz
import logging

def fetch_rss_entries(feed_url, current_week_range):
    entries = []
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        entry_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            entry_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            entry_date = datetime(*entry.updated_parsed[:6], tzinfo=pytz.UTC)
        else:
            logging.warning(f"Entry missing both 'published_parsed' and 'updated_parsed' in feed: {feed_url}")
            continue  # Skip if both dates are missing

        if current_week_range[0] <= entry_date < current_week_range[1]:
            entry_data = {
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', '#'),
                'published_parsed': entry_date,
                'provider_name': extract_provider_name(feed_url)
            }
            entries.append(entry_data)
            logging.info(f"Added RSS entry: {entry_data['title']} from {feed_url}")
    return entries

def extract_provider_name(feed_url):
    # Implement logic to extract provider name from feed URL
    # This is a placeholder implementation
    return feed_url.split('//')[-1].split('/')[0].replace('www.', '').capitalize()
