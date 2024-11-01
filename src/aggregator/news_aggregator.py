# src/aggregator/news_aggregator.py
from .config_loader import load_config
from .feed_fetcher import fetch_rss_entries
from .manual_fetcher import fetch_manual_entries
from datetime import datetime, timedelta
import pytz
import logging

class NewsAggregator:
    def __init__(self, config):
        self.config = config
        self.entries = []
        self.current_week_range = self.get_week_range()

    def get_week_range(self):
        today = datetime.now(pytz.UTC)
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday)
        last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_friday = last_friday + timedelta(days=7)
        logging.info(f"Current week range: {last_friday} to {next_friday}")
        return last_friday, next_friday

    def aggregate(self):
        # Fetch RSS feeds
        for feed in self.config.get('rss_feeds', []):
            self.entries.extend(fetch_rss_entries(feed, self.current_week_range))
        
        # Fetch manual sources
        for source in self.config.get('manual_sources', []):
            self.entries.extend(fetch_manual_entries(source, self.current_week_range))
        
        logging.info(f"Total entries fetched: {len(self.entries)}")
        return self.entries
