import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from .feed_fetcher import FeedFetcher
from .manual_fetcher import ManualFetcher

class NewsAggregator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feed_fetcher = FeedFetcher()
        self.manual_fetcher = ManualFetcher()
        self.current_week_range = self._calculate_date_range()

    def aggregate(self) -> List[Dict[str, Any]]:
        """Aggregate news from all configured sources."""
        entries = []
        
        # Process all source categories
        for category, sources in self.config['sources'].items():
            for source in sources:
                try:
                    source_entries = self._fetch_source(source)
                    for entry in source_entries:
                        entry['source_type'] = category  # Add source category
                        entry['source_metadata'] = {
                            'type': source.get('type', ''),
                            'status_url': source.get('status_url', ''),
                            'name': source.get('name', '')
                        }
                        entries.append(entry)
                except Exception as e:
                    logging.error(f"Error fetching from {source.get('name', 'unknown')}: {e}")

        # Sort entries by date
        entries.sort(key=lambda x: x.get('published', ''), reverse=True)
        return entries

    def _fetch_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch entries from a single source."""
        url = source.get('url', '')
        if not url:
            return []

        # Handle manual sources
        if source.get('manual', False):
            entries = self.manual_fetcher.fetch(url)
        else:
            entries = self.feed_fetcher.fetch(url)

        # Filter entries by date and keywords
        filtered_entries = []
        for entry in entries:
            # Add source information
            entry['provider_name'] = source.get('provider_name', '')
            entry['source_name'] = source.get('name', '')

            # Check if entry is within date range
            pub_date = self._parse_date(entry.get('published', ''))
            if not pub_date or not self._is_within_date_range(pub_date):
                continue

            # Apply keyword filtering if specified
            if 'filter_keywords' in source:
                if not self._matches_keywords(entry, source['filter_keywords']):
                    continue

            filtered_entries.append(entry)

        return filtered_entries

    def _calculate_date_range(self) -> tuple:
        """Calculate the date range based on config settings."""
        weeks = self.config.get('settings', {}).get('weeks_to_fetch', 1)
        end_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=7)  # End date is next week
        start_date = end_date - timedelta(weeks=weeks)
        return (start_date, end_date)

    def _is_within_date_range(self, date: datetime) -> bool:
        """Check if a date falls within the configured range."""
        return self.current_week_range[0] <= date <= self.current_week_range[1]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logging.error(f"Failed to parse date: {date_str}")
            return None

    def _matches_keywords(self, entry: Dict[str, Any], keywords: List[str]) -> bool:
        """Check if entry matches any of the filter keywords."""
        content = (
            str(entry.get('title', '')).lower() + 
            str(entry.get('content', '')).lower()
        )
        return any(keyword.lower() in content for keyword in keywords)
