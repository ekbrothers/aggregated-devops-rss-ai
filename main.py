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

    def _get_weekly_date_range(self):
        """Get date range for the current week (Friday to Friday)"""
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
        """Check if entry falls within the current week's range"""
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

    def analyze_with_claude(self, entries: List[Dict]) -> Dict:
        """Analyze entries with Claude to extract key information"""
        prompt = f"""Please analyze these DevOps updates from the past week and provide:
1. A concise executive summary highlighting the most critical updates (2-3 sentences)
2. Categorized insights:
   - Major Features (max 3)
   - Breaking Changes & Deprecations (max 3)
   - Security & Performance Updates (max 2)
3. Specific action items for DevOps teams (max 3)

Content: {json.dumps(entries, indent=2)}

Return as JSON with these keys: executive_summary, major_features, breaking_changes, security_performance, action_items"""

        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content)

    def generate_rss_feed(self):
        try:
            os.makedirs('dist', exist_ok=True)
            with open('dist/feed.xml', 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<feed xmlns="http://www.w3.org/2005/Atom">\n')
                f.write('<title>DevOps Weekly Update</title>\n')
                f.write('<link href="https://example.com/feed.xml" rel="self"/>\n')
                f.write(f"<updated>{datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>\n")
                f.write('<author><name>DevOps News Aggregator</name></author>\n')
                f.write('<id>urn:uuid:devops-news-aggregator</id>\n')

                # Add analyzed summary as first entry
                analysis = self.analyze_with_claude(self.entries)
                f.write('<entry>\n')
                f.write('<title>Weekly DevOps Summary</title>\n')
                f.write(f"<id>weekly-summary-{datetime.now(pytz.utc).strftime('%Y%m%d')}</id>\n")
                f.write(f"<updated>{datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>\n")
                f.write('<content type="html"><![CDATA[')
                f.write(f"<h2>Executive Summary</h2><p>{analysis['executive_summary']}</p>")
                f.write('<h3>Key Updates</h3><ul>')
                for feature in analysis['major_features']:
                    f.write(f'<li>{feature}</li>')
                f.write('</ul>')
                f.write('<h3>Action Items</h3><ul>')
                for item in analysis['action_items']:
                    f.write(f'<li>{item}</li>')
                f.write('</ul>')
                f.write(']]></content>\n')
                f.write('</entry>\n')

                # Add individual entries
                for entry in self.entries:
                    provider_name = entry.get('provider_name', 'Unknown Provider')
                    title = f"{provider_name}: {entry.get('title', 'Untitled')}"
                    link = entry.get('link', '#')
                    published = datetime(*entry.get('published_parsed', datetime.now(pytz.UTC).timetuple())[:6]).strftime('%Y-%m-%dT%H:%M:%SZ')
                    content = entry.get('summary', 'No content available')
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

    def generate_html_newsletter(self):
        try:
            os.makedirs('dist', exist_ok=True)
            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>DevOps Weekly Update</title>
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            </head>
            <body class="bg-gray-50">
                <div class="max-w-4xl mx-auto py-12 px-4">
                    <!-- Header -->
                    <div class="bg-white rounded-lg shadow-lg p-8 mb-8">
                        <h1 class="text-4xl font-bold text-gray-900 mb-4">DevOps Weekly Update</h1>
                        <p class="text-gray-600">{{ date_range }}</p>
                    </div>

                    <!-- Executive Summary -->
                    <div class="bg-blue-50 rounded-lg shadow p-6 mb-8">
                        <h2 class="text-2xl font-semibold text-blue-900 mb-4">
                            <i class="fas fa-star mr-2"></i>Summary
                        </h2>
                        <p class="text-gray-800">{{ analysis.executive_summary }}</p>
                    </div>

                    <!-- Key Updates Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <!-- Major Features -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-xl font-semibold text-gray-900 mb-4">
                                <i class="fas fa-rocket mr-2 text-blue-600"></i>Major Features
                            </h3>
                            <ul class="space-y-3">
                                {% for feature in analysis.major_features %}
                                <li class="flex items-start">
                                    <span class="text-blue-600 mr-2">•</span>
                                    {{ feature }}
                                </li>
                                {% endfor %}
                            </ul>
                        </div>

                        <!-- Breaking Changes -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-xl font-semibold text-gray-900 mb-4">
                                <i class="fas fa-exclamation-triangle mr-2 text-orange-600"></i>Breaking Changes
                            </h3>
                            <ul class="space-y-3">
                                {% for change in analysis.breaking_changes %}
                                <li class="flex items-start">
                                    <span class="text-orange-600 mr-2">•</span>
                                    {{ change }}
                                </li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>

                    <!-- Action Items -->
                    <div class="bg-white rounded-lg shadow p-6 mb-8">
                        <h3 class="text-xl font-semibold text-gray-900 mb-4">
                            <i class="fas fa-tasks mr-2 text-green-600"></i>Action Items
                        </h3>
                        <ul class="space-y-3">
                            {% for item in analysis.action_items %}
                            <li class="flex items-start">
                                <span class="text-green-600 mr-2">→</span>
                                {{ item }}
                            </li>
                            {% endfor %}
                        </ul>
                    </div>

                    <!-- All Updates -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-xl font-semibold text-gray-900 mb-6">
                            <i class="fas fa-list-alt mr-2 text-purple-600"></i>Full Updates
                        </h3>
                        <div class="space-y-6">
                            {% for update in entries %}
                            <div class="border-l-4 border-purple-200 pl-4">
                                <h4 class="font-semibold text-lg text-gray-900">{{ update.provider_name }}</h4>
                                <p class="text-gray-700 mb-2">{{ update.title }}</p>
                                <a href="{{ update.link }}" class="text-blue-600 hover:text-blue-800 text-sm">
                                    Read more <i class="fas fa-external-link-alt ml-1"></i>
                                </a>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            analysis = self.analyze_with_claude(self.entries)
            date_range = f"{self.weekly_date_range['start'].strftime('%B %d')} - {self.weekly_date_range['end'].strftime('%B %d, %Y')}"
            
            template = Template(template_str)
            html_content = template.render(
                entries=self.entries,
                analysis=analysis,
                date_range=date_range
            )
            
            with open('dist/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info("HTML newsletter generated successfully")
        except Exception as e:
            logging.error(f"Error generating HTML newsletter: {str(e)}")

    def run(self):
        self.fetch_rss_feeds()
        self.fetch_manual_sources()
        self.generate_html_newsletter()
        self.generate_rss_feed()
        with open('dist/.nojekyll', 'w') as f:
            pass
        logging.info("DevOps News Aggregator completed successfully")

if __name__ == "__main__":
    aggregator = DevOpsNewsAggregator()
    aggregator.run()
