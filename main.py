# main.py
import feedparser
import requests
from datetime import datetime
import pytz
from anthropic import Anthropic
import json
import os
from typing import Dict, List
import yaml
import logging
from bs4 import BeautifulSoup
import markdown

class DevOpsNewsAggregator:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
        self.feeds = self._load_config()
        self.entries = []
        self.important_updates = []

    def _load_config(self) -> Dict:
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)

    def fetch_rss_feeds(self):
        for feed_url, config in self.feeds['rss_feeds'].items():
            try:
                response = requests.get(feed_url)
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    entry['provider_name'] = config['name']
                    entry.published_parsed = entry.get('published_parsed', entry.get('updated_parsed'))
                    self.entries.append(entry)
            except Exception as e:
                logging.error(f"Error fetching {feed_url}: {str(e)}")

    def fetch_manual_sources(self):
        for source in self.feeds['manual_sources']:
            try:
                response = requests.get(source['url'])
                # Add custom scraping logic for each source
                if 'chatgpt' in source['name'].lower():
                    self._parse_openai_updates(response.text)
                # Add more source-specific parsers as needed
            except Exception as e:
                logging.error(f"Error fetching {source['name']}: {str(e)}")

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

    def generate_html_newsletter(self):
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Weekly Update</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100 p-8">
            <div class="max-w-4xl mx-auto">
                <h1 class="text-3xl font-bold mb-8">DevOps Weekly Update</h1>
                <div class="space-y-8">
                    {% for update in important_updates %}
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h2 class="text-xl font-semibold mb-2">{{ update.title }}</h2>
                        <div class="text-gray-600 mb-4">{{ update.summary }}</div>
                        <div class="mb-4">
                            <span class="px-2 py-1 rounded text-sm font-medium
                                {% if update.impact_level == 'HIGH' %}bg-red-100 text-red-800
                                {% elif update.impact_level == 'MEDIUM' %}bg-yellow-100 text-yellow-800
                                {% else %}bg-green-100 text-green-800{% endif %}">
                                {{ update.impact_level }} Impact
                            </span>
                        </div>
                        <div class="mb-4">
                            <h3 class="font-medium mb-2">Action Items:</h3>
                            <ul class="list-disc pl-5">
                                {% for item in update.action_items %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        <div class="text-sm text-gray-500">
                            Related: {{ update.related_tech|join(', ') }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """
        # Implementation continues...

    def run(self):
        self.fetch_rss_feeds()
        self.fetch_manual_sources()
        self.generate_html_newsletter()
        self.generate_rss_feed()

if __name__ == "__main__":
    aggregator = DevOpsNewsAggregator()
    aggregator.run()
