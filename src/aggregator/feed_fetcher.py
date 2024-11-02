import feedparser
import logging
from datetime import datetime
import pytz
from typing import List, Dict, Any, Tuple
from bs4 import BeautifulSoup
import re

class FeedFetcher:
    def __init__(self):
        self.cache = {}

    def fetch(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse RSS/Atom feed from the given URL.
        
        Args:
            url: The URL of the feed to fetch
            
        Returns:
            List of parsed entries
        """
        try:
            logging.debug(f"Fetching feed from {url}")
            feed = feedparser.parse(url)
            
            if feed.get('status', 200) >= 400:
                logging.error(f"Failed to fetch feed from {url} - Status: {feed.get('status')}")
                return []
            
            entries = []
            for entry in feed.entries:
                try:
                    # Extract content
                    content = self._extract_content(entry)
                    
                    # Parse and standardize date
                    published = self._parse_date(entry)
                    
                    # Create standardized entry
                    processed_entry = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': published,
                        'content': content
                    }
                    
                    entries.append(processed_entry)
                    
                except Exception as e:
                    logging.error(f"Error processing entry from {url}: {e}")
                    continue
            
            return entries
            
        except Exception as e:
            logging.error(f"Error fetching feed from {url}: {e}")
            return []

    def _extract_content(self, entry: Dict) -> str:
        """
        Extract content from a feed entry, handling different content formats.
        """
        # Try different content fields
        if 'content' in entry:
            if isinstance(entry.content, list):
                content = entry.content[0].value
            else:
                content = entry.content
        elif 'summary' in entry:
            content = entry.summary
        elif 'description' in entry:
            content = entry.description
        else:
            content = ''

        # Clean HTML if present
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)

        return content

    def _parse_date(self, entry: Dict) -> str:
        """
        Parse and standardize the publication date from an entry.
        """
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if hasattr(entry, field):
                try:
                    # Parse the date string to a datetime object
                    if field + '_parsed' in entry:
                        dt = datetime(*entry[field + '_parsed'][:6])
                    else:
                        # Try parsing the date string directly
                        dt = datetime.strptime(getattr(entry, field), '%Y-%m-%dT%H:%M:%SZ')
                    
                    # Ensure timezone awareness
                    if dt.tzinfo is None:
                        dt = pytz.UTC.localize(dt)
                    
                    # Return ISO format string
                    return dt.isoformat()
                except Exception as e:
                    logging.debug(f"Failed to parse date from {field}: {e}")
                    continue
        
        # If no valid date found, use current time
        return datetime.now(pytz.UTC).isoformat()

def fetch_rss_entries(feed_url: str, week_range: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
    """
    Fetch entries from an RSS feed within the specified date range.
    Maintained for backward compatibility.
    """
    fetcher = FeedFetcher()
    return fetcher.fetch(feed_url)
