# main.py
import feedparser
import requests
from datetime import datetime, timedelta
import pytz
from anthropic import Anthropic
import json
import os
from typing import Dict, List
import yaml
import logging
from bs4 import BeautifulSoup
import markdown
from jinja2 import Template

class DevOpsNewsAggregator:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.feeds = self._load_config()
        self.entries = []
        self.important_updates = []
        self.weekly_date_range = self._get_weekly_date_range()
        logging.basicConfig(level=logging.INFO)
        
        # Create dist directory at initialization
        os.makedirs('dist', exist_ok=True)
        logging.info("Initialized dist directory")

    def _get_weekly_date_range(self):
        today = datetime.now(pytz.UTC)
        last_friday = today - timedelta(days=(today.weekday() + 3) % 7)
        return {
            'start': last_friday - timedelta(days=7),
            'end': last_friday
        }

    def _load_config(self) -> Dict:
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)

    def _is_within_week(self, entry_date):
        if not entry_date:
            return False
        entry_datetime = datetime(*entry_date[:6], tzinfo=pytz.UTC)
        return self.weekly_date_range['start'] <= entry_datetime <= self.weekly_date_range['end']

    def fetch_rss_feeds(self):
        for feed_url, config in self.feeds['rss_feeds'].items():
            try:
                response = requests.get(feed_url)
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    if self._is_within_week(entry.get('published_parsed', entry.get('updated_parsed'))):
                        entry['provider_name'] = config['name']
                        entry.published_parsed = entry.get('published_parsed', entry.get('updated_parsed'))
                        self.entries.append(entry)
            except Exception as e:
                logging.error(f"Error fetching {feed_url}: {str(e)}")

    def analyze_with_claude(self, content: str) -> Dict:
        prompt = f"""Please analyze this DevOps update and provide:
1. A brief summary (2-3 sentences)
2. Impact level (HIGH/MEDIUM/LOW)
3. Action items for DevOps teams
4. Related technologies or services

Content: {content}

Format the response as JSON with keys: summary, impact_level, action_items, related_tech"""

        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content)

    def fetch_manual_sources(self):
        for source in self.feeds['manual_sources']:
            try:
                response = requests.get(source['url'])
                if 'chatgpt' in source['name'].lower():
                    self._parse_openai_updates(response.text)
                elif 'claude' in source['name'].lower():
                    self._parse_claude_updates(response.text)
            except Exception as e:
                logging.error(f"Error fetching {source['name']}: {str(e)}")

    def _parse_openai_updates(self, content: str):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            updates = soup.find_all('div', class_='release-note')
            for update in updates:
                entry = {
                    'title': update.find('h2').text.strip(),
                    'summary': update.find('div', class_='content').text.strip(),
                    'published_parsed': datetime.now(pytz.UTC).timetuple(),
                    'provider_name': 'ChatGPT Updates',
                    'link': 'https://help.openai.com/en/articles/6825453-chatgpt-release-notes'
                }
                if self._is_within_week(entry['published_parsed']):
                    self.entries.append(entry)
        except Exception as e:
            logging.error(f"Error parsing OpenAI updates: {str(e)}")

    def _parse_claude_updates(self, content: str):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            updates = soup.find_all('article')
            for update in updates:
                entry = {
                    'title': update.find('h2').text.strip(),
                    'summary': update.find('div', class_='content').text.strip(),
                    'published_parsed': datetime.now(pytz.UTC).timetuple(),
                    'provider_name': 'Claude Updates',
                    'link': 'https://www.anthropic.com/news'
                }
                if self._is_within_week(entry['published_parsed']):
                    self.entries.append(entry)
        except Exception as e:
            logging.error(f"Error parsing Claude updates: {str(e)}")

    def generate_html_newsletter(self):
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Weekly Update</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100 p-8">
            <div class="max-w-4xl mx-auto">
                <h1 class="text-3xl font-bold mb-8">DevOps Weekly Update</h1>
                <p class="text-gray-600 mb-8">{{ date_range }}</p>
                
                <!-- Summary Section -->
                <div class="bg-blue-50 rounded-lg p-6 mb-8">
                    <h2 class="text-2xl font-semibold mb-4">Weekly Summary</h2>
                    <div class="prose">{{ summary }}</div>
                </div>

                <!-- Updates List -->
                <div class="space-y-8">
                    {% for update in entries %}
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h2 class="text-xl font-semibold mb-2">{{ update.provider_name }}: {{ update.title }}</h2>
                        <div class="text-gray-600 mb-4">{{ update.summary }}</div>
                        <div class="text-sm text-gray-500">
                            <a href="{{ update.link }}" class="text-blue-500 hover:text-blue-700">Read more →</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            date_range = f"{self.weekly_date_range['start'].strftime('%B %d')} - {self.weekly_date_range['end'].strftime('%B %d, %Y')}"
            
            # Create a summary of all entries
            all_content = "\n".join([f"{entry.get('title', '')}\n{entry.get('summary', '')}" for entry in self.entries])
            analysis = self.analyze_with_claude(all_content)
            
            template = Template(template_str)
            html_content = template.render(
                entries=self.entries,
                date_range=date_range,
                summary=analysis.get('summary', 'No updates this week.')
            )
            
            with open('dist/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info("HTML newsletter generated successfully")
        except Exception as e:
            logging.error(f"Error generating HTML newsletter: {str(e)}")

    def generate_rss_feed(self):
        try:
            with open('dist/feed.xml', 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<feed xmlns="http://www.w3.org/2005/Atom">\n')
                f.write('<title>DevOps Weekly Update</title>\n')
                f.write('<link href="https://example.com/feed.xml" rel="self"/>\n')
                f.write(f"<updated>{datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>\n")
                f.write('<author><name>DevOps News Aggregator</name></author>\n')
                f.write('<id>urn:uuid:devops-news-aggregator</id>\n')

                for entry in self.entries:
                    provider_name = entry.get('provider_name', 'Unknown Provider')
                    title = f"{provider_name}: {entry.get('title', 'Untitled')}"
                    link = entry.get('link', '#')
                    published = datetime(*entry.get('published_parsed', datetime.now(pytz.UTC).timetuple())[:6]).strftime('%Y-%m-%dT%H:%M:%SZ')
                    content = entry.get('summary', 'No content available')
                    
                    # Clean content for XML
                    content = content.replace('<![CDATA[', '').replace(']]>', '')
                    
                    f.write('<entry>\n')
                    f.write(f"<title>{title}</title>\n")
                    f.write(f"<link href='{link}'/>\n")
                    f.write(f"<id>{link}</id>\n")
                    f.write(f"<updated>{published}</updated>\n")
                    f.write(f"<content type='html'><![CDATA[{content}]]></content>\n")
                    f.write('</entry>\n')
                
                f.write('</feed>')
            logging.info("RSS feed generated successfully")
        except Exception as e:
            logging.error(f"Error generating RSS feed: {str(e)}")

    def run(self):
        self.fetch_rss_feeds()
        self.fetch_manual_sources()
        self.generate_html_newsletter()
        self.generate_rss_feed()
        # Create .nojekyll file
        with open('dist/.nojekyll', 'w') as f:
            pass
        logging.info("DevOps News Aggregator completed successfully")

if __name__ == "__main__":
    aggregator = DevOpsNewsAggregator()
    aggregator.run()
