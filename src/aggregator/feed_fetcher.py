import feedparser
from datetime import datetime
import pytz
import logging

def fetch_rss_entries(feed_url, current_week_range, source_config):
    """
    Fetch and parse RSS/Atom feed entries.
    """
    entries = []
    try:
        feed = feedparser.parse(feed_url)
        
        if hasattr(feed, 'status') and feed.status >= 400:
            logging.error(f"Failed to fetch feed from {feed_url} - Status: {feed.status}")
            return entries

        for entry in feed.entries:
            try:
                # Extract dates
                entry_date = _parse_entry_date(entry)
                if not entry_date:
                    continue

                # Only process if within date range
                if current_week_range[0] <= entry_date < current_week_range[1]:
                    # Extract content based on content type
                    content = _extract_entry_content(entry, source_config.get('content_type', 'html'))
                    
                    # Create entry data
                    entry_data = {
                        'title': entry.get('title', 'No Title'),
                        'link': entry.get('link', '#'),
                        'published': entry_date.isoformat(),
                        'content': content,
                        'content_type': source_config.get('content_type', 'html'),
                        'provider_name': extract_provider_name(feed_url)
                    }
                    
                    entries.append(entry_data)
                    logging.info(f"Added RSS entry: {entry_data['title']} from {feed_url}")

            except Exception as e:
                logging.error(f"Error processing entry from {feed_url}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
    
    return entries

def _parse_entry_date(entry):
    """
    Parse the publication date from an entry.
    """
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=pytz.UTC)
    return None

def _extract_entry_content(entry, content_type):
    """
    Extract content from an entry while preserving specified format.
    """
    content = ''
    
    # Try different content fields
    if hasattr(entry, 'content'):
        if isinstance(entry.content, list):
            content = entry.content[0].value
        else:
            content = entry.content
    elif hasattr(entry, 'summary'):
        content = entry.summary
    elif hasattr(entry, 'description'):
        content = entry.description
    
    # For markdown content, we want to preserve the original formatting
    # GitHub and some other platforms provide content in markdown format
    if content_type == 'markdown':
        # If content is HTML but source is markdown (common with GitHub),
        # we might need to add processing here to convert HTML back to markdown
        # For now, we'll preserve the content as-is since GitHub's HTML
        # is typically a good representation of the markdown
        pass
    elif content_type == 'plain':
        # For plain text, strip HTML tags if present
        from bs4 import BeautifulSoup
        if content:
            content = BeautifulSoup(content, 'html.parser').get_text()
    # For HTML content_type, keep the HTML as-is
    
    return content

def extract_provider_name(feed_url):
    """
    Extract provider name from feed URL.
    """
    # Extract domain from URL
    domain = feed_url.split('//')[-1].split('/')[0].lower()
    
    # Handle known providers
    if 'github' in domain:
        if 'blog' in domain:
            return 'github.blog'
        return 'github.com'
    elif 'gitlab' in domain:
        return 'gitlab'
    elif 'azure' in domain or 'microsoft' in domain:
        return 'azuredevops'
    elif 'hashicorp' in domain:
        return 'hashicorp'
    elif 'google' in domain:
        return 'googlecloud'
    elif 'anthropic' in domain:
        return 'anthropic'
    elif 'openai' in domain:
        return 'openai'
    
    # Remove www. and .com/.org/etc
    provider = domain.replace('www.', '').split('.')[0]
    return provider
