from datetime import datetime, timedelta
import pytz
import logging
from typing import List, Dict, Any, Tuple
from .feed_fetcher import FeedFetcher, fetch_rss_entries
from .manual_fetcher import fetch_manual_entries

class NewsAggregator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feed_fetcher = FeedFetcher()
        self.current_week_range = self._get_week_range()
        self.entries = []

    def _get_week_range(self) -> Tuple[datetime, datetime]:
        """
        Get the date range for fetching updates.
        Default to 2 weeks of updates.
        """
        today = datetime.now(pytz.UTC)
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday + 7)  # Go back an extra week
        last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_friday = last_friday + timedelta(days=14)  # Two weeks range
        logging.info(f"Current week range: {last_friday} to {next_friday}")
        return last_friday, next_friday

    def aggregate(self) -> List[Dict[str, Any]]:
        """
        Aggregate news from all configured sources.
        """
        entries = []

        # Fetch RSS feeds
        for feed_url, feed_config in self.config.get('rss_feeds', {}).items():
            try:
                feed_entries = self.feed_fetcher.fetch(feed_url)
                for entry in feed_entries:
                    # Add source metadata
                    entry['provider_name'] = feed_config.get('provider_name', '')
                    entry['importance_keywords'] = feed_config.get('importance_keywords', [])
                    entry['source_type'] = self._determine_source_type(feed_config)
                    entries.append(entry)
            except Exception as e:
                logging.error(f"Error fetching RSS feed {feed_url}: {e}")

        # Fetch manual sources
        for source in self.config.get('manual_sources', []):
            try:
                manual_entries = fetch_manual_entries(source, self.current_week_range)
                for entry in manual_entries:
                    # Add source metadata
                    entry['provider_name'] = source.get('provider_name', '')
                    entry['source_type'] = self._determine_source_type(source)
                    entries.append(entry)
            except Exception as e:
                logging.error(f"Error fetching manual source {source.get('url', '')}: {e}")

        # Filter entries by date
        filtered_entries = self._filter_entries_by_date(entries)
        
        # Sort entries by date
        filtered_entries.sort(
            key=lambda x: datetime.fromisoformat(x.get('published', '2000-01-01')),
            reverse=True
        )

        logging.info(f"Total entries fetched: {len(filtered_entries)}")
        return filtered_entries

    def _determine_source_type(self, source_config: Dict[str, Any]) -> str:
        """
        Determine the type of source based on provider name and URL.
        """
        provider = source_config.get('provider_name', '').lower()
        
        # Terraform providers and tools
        if provider == 'terraform':
            if 'provider' in str(source_config.get('url', '')):
                return 'terraform_providers'
            return 'devops_tools'
        
        # VCS platforms
        if provider in ['github', 'gitlab', 'azuredevops']:
            return 'vcs_platforms'
        
        # AI tools
        if provider in ['openai', 'anthropic']:
            return 'ai_tools'
        
        # Cloud providers
        if provider in ['googlecloud', 'aws', 'azure']:
            return 'cloud_providers'
        
        # Default to devops_tools
        return 'devops_tools'

    def _filter_entries_by_date(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter entries to only include those within the current date range.
        """
        filtered = []
        for entry in entries:
            try:
                pub_date = datetime.fromisoformat(entry.get('published', '2000-01-01'))
                if self.current_week_range[0] <= pub_date <= self.current_week_range[1]:
                    filtered.append(entry)
            except (ValueError, TypeError) as e:
                logging.error(f"Error parsing date for entry: {e}")
                continue
        return filtered
