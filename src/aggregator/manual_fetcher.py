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
        
        # Remove unnecessary elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
            
        # Get main content based on provider
        provider = source.get('provider_name', '').lower()
        if provider == 'azuredevops':
            # Azure DevOps specific parsing
            content_elements = soup.select('article') or soup.select('.content-article')
        elif provider == 'openai':
            # OpenAI specific parsing
            content_elements = soup.select('article') or soup.select('.article-content')
        elif provider == 'anthropic':
            # Anthropic specific parsing
            content_elements = soup.select('article') or soup.select('.blog-post')
        else:
            # Default to main content areas
            content_elements = soup.select('main') or soup.select('article') or [soup]
            
        # Process each content element
        for element in content_elements:
            # Preserve HTML content
            content = str(element)
            if not content:
                continue
                
            entry_date = datetime.now(pytz.UTC)  # Use current date as fallback
            
            # Try to find a date in the content
            date_element = element.select_one('time') or element.select_one('.date') or element.select_one('.published')
            if date_element and date_element.get('datetime'):
                try:
                    entry_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            if current_week_range[0] <= entry_date < current_week_range[1]:
                # Try to find a title
                title_element = element.select_one('h1') or element.select_one('h2')
                title = title_element.get_text(strip=True) if title_element else source.get('name', 'No Title')
                
                entry = {
                    'title': title,
                    'link': source['url'],
                    'content': content,  # Keep full HTML content
                    'published': entry_date.isoformat(),
                    'provider_name': source.get('provider_name', 'Unknown Platform')
                }
                entries.append(entry)
                logging.info(f"Added manual entry: {entry['title']} from {source['url']}")
                
    except requests.RequestException as e:
        logging.error(f"Failed to fetch manual source: {source['url']} - {str(e)}")
    return entries
