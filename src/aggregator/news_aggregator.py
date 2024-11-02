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
        
        # Process RSS feeds
        for feed_url, feed_config in self.config.get('rss_feeds', {}).items():
            try:
                feed_entries = fetch_rss_entries(feed_url, self.current_week_range)
                for entry in feed_entries:
                    # Add source configuration
                    entry['provider_name'] = feed_config.get('provider_name', entry.get('provider_name', ''))
                    entry['importance_keywords'] = feed_config.get('importance_keywords', [])
                    
                    # Determine source type
                    entry['source_type'] = self._determine_source_type(
                        entry['provider_name'],
                        feed_url,
                        feed_config
                    )
                    
                    entries.append(entry)
                    logging.debug(f"Processed entry: {entry.get('title')} from {feed_url}")
                    
            except Exception as e:
                logging.error(f"Error processing RSS feed {feed_url}: {e}")
        
        # Process manual sources
        for source in self.config.get('manual_sources', []):
            try:
                manual_entries = fetch_manual_entries(source, self.current_week_range)
                for entry in manual_entries:
                    # Add source information
                    entry['provider_name'] = source.get('provider_name', '')
                    entry['source_type'] = self._determine_source_type(
                        entry['provider_name'],
                        source.get('url', ''),
                        source
                    )
                    
                    entries.append(entry)
                    logging.debug(f"Processed manual entry from {source.get('url')}")
                    
            except Exception as e:
                logging.error(f"Error processing manual source {source.get('url', '')}: {e}")

        # Sort entries by date
        entries.sort(
            key=lambda x: datetime.fromisoformat(x['published']) if isinstance(x.get('published'), str)
            else x.get('published', datetime.min.replace(tzinfo=pytz.UTC)),
            reverse=True
        )

        logging.info(f"Total entries fetched: {len(entries)}")
        return entries

    def _determine_source_type(self, provider_name, url, config):
        """
        Determine the type of source based on provider and URL.
        """
        provider = provider_name.lower()
        url = url.lower()
        
        # Terraform providers
        if 'terraform-provider-' in url:
            return 'terraform_providers'
        
        # Terraform core
        if provider == 'terraform' and 'provider' not in url:
            return 'devops_tools'
        
        # VCS platforms
        if provider in ['github', 'gitlab', 'azuredevops'] or any(p in url for p in ['github', 'gitlab', 'azure.com']):
            return 'vcs_platforms'
        
        # AI tools
        if provider in ['openai', 'anthropic', 'claude'] or 'copilot' in url:
            return 'ai_tools'
        
        # Cloud providers
        if provider in ['googlecloud', 'aws', 'azure'] or any(p in url for p in ['google.com', 'aws.amazon.com', 'azure.com']):
            return 'cloud_providers'
        
        # HashiCorp tools
        if provider == 'hashicorp' or 'hashicorp.com' in url:
            return 'devops_tools'
        
        return 'other'
