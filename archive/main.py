import feedparser
import requests
from datetime import datetime, timedelta
import pytz
import os
import yaml
import logging
from bs4 import BeautifulSoup
from jinja2 import Template
from analyze_with_claude import analyze_with_claude  # Import the function

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DevOpsNewsAggregator:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.feeds = self._load_config()
        self.entries = []
        self.current_week_range = self._get_week_range()
    
    def _load_config(self):
        """Load RSS feeds and other settings from config.yml"""
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)

    def _get_week_range(self):
        """Get the date range for the current week (Friday to Friday)"""
        today = datetime.now(pytz.UTC)
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday)
        last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_friday = last_friday + timedelta(days=7)
        return last_friday, next_friday

    def _is_in_current_week(self, entry_date):
        """Check if an entry falls within the current week range"""
        return self.current_week_range[0] <= entry_date < self.current_week_range[1]
        
    def fetch_rss_feeds(self):
        """Fetch entries from RSS feeds defined in the config"""
        for feed_url in self.feeds['rss_feeds']:
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
                
                if self._is_in_current_week(entry_date):
                    self.entries.append(entry)
                    logging.info(f"Added entry: {entry.get('title', 'No Title')} from {feed_url}")

    def fetch_manual_sources(self):
        """Fetch updates from sources that require web scraping"""
        for source in self.feeds['manual_sources']:
            if not all(key in source for key in ['url', 'title', 'provider_name']):
                logging.error(f"Manual source is missing required fields: {source}")
                continue
    
            try:
                response = requests.get(source['url'])
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                content = soup.get_text()
                entry = {
                    'title': source['title'],
                    'provider_name': source['provider_name'],
                    'link': source['url'],
                    'content': content,
                    'published_parsed': datetime.now(pytz.UTC).timetuple()
                }
                self.entries.append(entry)
                logging.info(f"Added manual entry: {source['title']} from {source['url']}")
            except requests.RequestException as e:
                logging.error(f"Failed to fetch manual source: {source['url']} - {str(e)}")

    def generate_html_newsletter(self):
        """Generate a detailed HTML newsletter using Jinja2 template, grouped by platform with summaries."""
        try:
            os.makedirs('dist', exist_ok=True)
            
            # Organize entries by platform
            platforms = {}
            for entry in self.entries:
                entry_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    entry_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    entry_date = datetime(*entry.updated_parsed[:6], tzinfo=pytz.UTC)
                else:
                    continue
    
                if not self._is_in_current_week(entry_date):
                    continue
    
                # Collect details from Claude's analysis or provide fallback data
                analysis = entry.get('analysis', {})
                summary = analysis.get('summary', "No summary available.")
                impact_level = analysis.get('impact_level', 'LOW')
                key_changes = analysis.get('key_changes', [])
                action_items = analysis.get('action_items', [])
                platform_name = entry.get('provider_name', 'Unknown Platform')
                platform_url = f"https://simpleicons.org/icons/{platform_name.lower().replace(' ', '')}.svg"
    
                # Organize by platform name
                if platform_name not in platforms:
                    platforms[platform_name] = {
                        "entries": [],
                        "icon_url": platform_url
                    }
                platforms[platform_name]["entries"].append({
                    "title": entry.get('title', 'No Title'),
                    "link": entry.get('link', '#'),
                    "summary": summary,
                    "impact_level": impact_level,
                    "key_changes": key_changes,
                    "action_items": action_items
                })
    
            # Render the HTML with the template
            start_date = self.current_week_range[0].strftime('%B %d, %Y')
            end_date = self.current_week_range[1].strftime('%B %d, %Y')
            template_data = {
                'week_range': f"{start_date} - {end_date}",
                'platforms': platforms
            }
    
            template_path = os.path.join(os.getcwd(), 'newsletter_template.html')
            if not os.path.isfile(template_path):
                logging.error(f"Template file not found at {template_path}")
                return
            
            with open(template_path, 'r') as f:
                template = Template(f.read())
    
            html_content = template.render(**template_data)
            output_path = 'dist/index.html'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
    
            logging.info("HTML newsletter generated successfully at dist/index.html")
        except Exception as e:
            logging.error(f"Error generating HTML newsletter: {str(e)}")


    def generate_rss_feed(self):
        """Generate RSS feed from the aggregated entries"""
        pass  # Implement if needed

    def run(self):
        """Main execution of aggregator"""
        self.fetch_rss_feeds()
        self.fetch_manual_sources()

        for entry in self.entries:
            entry_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                entry_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                entry_date = datetime(*entry.updated_parsed[:6], tzinfo=pytz.UTC)

            if entry_date and self._is_in_current_week(entry_date):
                entry['analysis'] = analyze_with_claude(
                    entry.get('content', ''),
                    entry.get('provider_name', 'Unknown'),
                    entry.get('title', 'Untitled'),
                    self.api_key
                )
                logging.info(f"Analyzed entry: {entry.get('title', 'No Title')} - Impact level: {entry['analysis'].get('impact_level', 'None')}")

        self.generate_html_newsletter()
        self.generate_rss_feed()
        logging.info("DevOps News Aggregator completed successfully")

if __name__ == "__main__":
    aggregator = DevOpsNewsAggregator()
    aggregator.run()
