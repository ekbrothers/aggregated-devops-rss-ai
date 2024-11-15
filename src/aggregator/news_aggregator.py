from datetime import datetime, timedelta
import pytz
import logging
from .feed_fetcher import fetch_rss_entries
from .manual_fetcher import fetch_manual_entries

class NewsAggregator:
    def __init__(self, config):
        self.config = config
        self.current_week_range = self._get_week_range()

    def _get_week_range(self):
        """
        Get date range for the last 2 weeks.
        """
        today = datetime.now(pytz.UTC)
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday + 7)  # Go back an extra week
        last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_friday = last_friday + timedelta(days=14)  # Two weeks range
        logging.info(f"Current week range: {last_friday} to {next_friday}")
        return last_friday, next_friday

    def aggregate(self):
        """
        Aggregate news from all configured sources.
        """
        entries = []
        sources = self.config.get('sources', {})
        
        # Process all source categories
        for category, source_list in sources.items():
            for source in source_list:
                try:
                    # Skip if no URL provided
                    if not source.get('url'):
                        continue
                        
                    # Set default content type if not specified
                    if 'content_type' not in source:
                        # GitHub-related sources typically provide markdown
                        if 'github.com' in source.get('url', ''):
                            source['content_type'] = 'markdown'
                        else:
                            source['content_type'] = 'html'
                    
                    # Determine if manual or RSS feed
                    if source.get('manual', False):
                        source_entries = fetch_manual_entries(source, self.current_week_range)
                    else:
                        source_entries = fetch_rss_entries(source['url'], self.current_week_range, source)
                    
                    # Process entries
                    for entry in source_entries:
                        # Add source information
                        entry['provider_name'] = source.get('provider_name', '')
                        entry['source_type'] = category
                        entry['content_type'] = source.get('content_type', 'html')
                        
                        entries.append(entry)
                        logging.debug(f"Processed {entry['content_type']} entry from {source.get('name', 'Unknown')} ({source.get('url')})")
                        
                except Exception as e:
                    logging.error(f"Error processing source {source.get('name', 'Unknown')} ({source.get('url')}): {e}")

        # Sort entries by date
        entries.sort(
            key=lambda x: datetime.fromisoformat(x['published']) if isinstance(x.get('published'), str)
            else x.get('published', datetime.min.replace(tzinfo=pytz.UTC)),
            reverse=True
        )

        logging.info(f"Total entries fetched: {len(entries)}")
        return entries
