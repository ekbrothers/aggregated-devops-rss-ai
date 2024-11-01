# main.py
import feedparser
import requests
from datetime import datetime, timedelta
import pytz
from anthropic import Anthropic
import json
import os
from typing import Dict, List, Optional
import yaml
import logging
from bs4 import BeautifulSoup
from jinja2 import Template
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Update:
    title: str
    summary: str
    provider_name: str
    link: str
    published_date: datetime
    impact_level: str
    category: str
    action_items: List[str]
    related_tech: List[str]

class DevOpsNewsAggregator:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.feeds = self._load_config()
        self.entries: List[Update] = []
        self.week_start = self._get_week_start()
        self.week_end = self.week_start + timedelta(days=7)
        logging.basicConfig(level=logging.INFO)

    def _get_week_start(self) -> datetime:
        """Get the start of the current week (Friday)"""
        today = datetime.now(pytz.UTC)
        # Get the most recent Friday
        days_since_friday = (today.weekday() - 4) % 7
        return (today - timedelta(days=days_since_friday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def _load_config(self) -> Dict:
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)

    def _is_within_week(self, date: datetime) -> bool:
        """Check if a date falls within the current week's range"""
        return self.week_start <= date < self.week_end

    def fetch_rss_feeds(self):
        for feed_url, config in self.feeds['rss_feeds'].items():
            try:
                response = requests.get(feed_url)
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    published = datetime(*entry.get('published_parsed', entry.get('updated_parsed'))[:6], tzinfo=pytz.UTC)
                    
                    if not self._is_within_week(published):
                        continue
                        
                    # Analyze with Claude
                    analysis = self.analyze_with_claude(f"{entry.get('title', '')} - {entry.get('summary', '')}")
                    
                    update = Update(
                        title=entry.get('title', 'Untitled'),
                        summary=analysis['summary'],
                        provider_name=config['name'],
                        link=entry.get('link', '#'),
                        published_date=published,
                        impact_level=analysis['impact_level'],
                        category=analysis['category'],
                        action_items=analysis['action_items'],
                        related_tech=analysis['related_tech']
                    )
                    self.entries.append(update)
                    
            except Exception as e:
                logging.error(f"Error fetching {feed_url}: {str(e)}")

    def analyze_with_claude(self, content: str) -> Dict:
        prompt = f"""Analyze this DevOps update and provide:
1. A concise 1-2 sentence summary focusing on the key impact
2. Impact level (HIGH/MEDIUM/LOW) based on urgency and scope
3. Category (SECURITY/FEATURE/PERFORMANCE/DEPRECATION)
4. Up to 3 specific action items for DevOps teams
5. Related technologies or services (up to 5)

Content: {content}

Format response as JSON with keys: summary, impact_level, category, action_items, related_tech"""

        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content)

    def generate_html_newsletter(self):
        try:
            os.makedirs('dist', exist_ok=True)
            
            # Group updates by category
            categorized_updates = defaultdict(list)
            for update in self.entries:
                categorized_updates[update.category].append(update)
            
            # Sort updates by impact level within each category
            impact_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            for category in categorized_updates:
                categorized_updates[category].sort(
                    key=lambda x: (impact_order[x.impact_level], x.published_date), 
                    reverse=True
                )

            # Get high-impact updates across all categories
            high_impact_updates = [
                update for update in self.entries 
                if update.impact_level == 'HIGH'
            ][:3]  # Top 3 high-impact updates

            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>DevOps Weekly Update</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://cdn.tailwindcss.com"></script>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            </head>
            <body class="bg-gray-50">
                <div class="max-w-6xl mx-auto px-4 py-8">
                    <!-- Header -->
                    <header class="mb-8">
                        <h1 class="text-4xl font-bold text-gray-900 mb-2">DevOps Weekly Digest</h1>
                        <p class="text-gray-600">
                            Week of {{ week_start.strftime('%B %d, %Y') }} to {{ week_end.strftime('%B %d, %Y') }}
                        </p>
                    </header>

                    <!-- Key Highlights -->
                    {% if high_impact_updates %}
                    <section class="mb-12">
                        <h2 class="text-2xl font-bold text-gray-900 mb-6">
                            <i class="fas fa-star text-yellow-500 mr-2"></i>Key Highlights
                        </h2>
                        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                            {% for update in high_impact_updates %}
                            <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
                                <h3 class="font-semibold text-lg mb-2">{{ update.title }}</h3>
                                <p class="text-gray-600 text-sm mb-4">{{ update.summary }}</p>
                                <div class="flex items-center justify-between">
                                    <span class="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                                        {{ update.category }}
                                    </span>
                                    <a href="{{ update.link }}" class="text-blue-600 hover:text-blue-800 text-sm">
                                        Read more <i class="fas fa-external-link-alt ml-1"></i>
                                    </a>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </section>
                    {% endif %}

                    <!-- Categorized Updates -->
                    {% for category, updates in categorized_updates.items() %}
                    <section class="mb-12">
                        <h2 class="text-2xl font-bold text-gray-900 mb-6">
                            <i class="fas fa-{{ 
                                'shield-alt' if category == 'SECURITY' else
                                'puzzle-piece' if category == 'FEATURE' else
                                'tachometer-alt' if category == 'PERFORMANCE' else
                                'exclamation-triangle'
                            }} mr-2"></i>
                            {{ category }} Updates
                        </h2>
                        <div class="space-y-6">
                            {% for update in updates %}
                            <div class="bg-white rounded-lg shadow-sm p-6">
                                <div class="flex items-start justify-between mb-4">
                                    <h3 class="font-semibold text-lg">{{ update.title }}</h3>
                                    <span class="px-2 py-1 rounded-full text-xs font-medium {{ 
                                        'bg-red-100 text-red-800' if update.impact_level == 'HIGH' else
                                        'bg-yellow-100 text-yellow-800' if update.impact_level == 'MEDIUM' else
                                        'bg-green-100 text-green-800'
                                    }}">
                                        {{ update.impact_level }}
                                    </span>
                                </div>
                                <p class="text-gray-600 mb-4">{{ update.summary }}</p>
                                
                                {% if update.action_items %}
                                <div class="mb-4">
                                    <h4 class="font-medium text-sm mb-2">Action Items:</h4>
                                    <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
                                        {% for item in update.action_items %}
                                        <li>{{ item }}</li>
                                        {% endfor %}
                                    </ul>
                                </div>
                                {% endif %}

                                <div class="flex items-center justify-between">
                                    <div class="flex flex-wrap gap-2">
                                        {% for tech in update.related_tech %}
                                        <span class="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                                            {{ tech }}
                                        </span>
                                        {% endfor %}
                                    </div>
                                    <a href="{{ update.link }}" 
                                       class="text-blue-600 hover:text-blue-800 text-sm flex items-center">
                                        Details <i class="fas fa-external-link-alt ml-1"></i>
                                    </a>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </section>
                    {% endfor %}
                </div>

                <footer class="bg-gray-100 border-t mt-12">
                    <div class="max-w-6xl mx-auto px-4 py-6">
                        <p class="text-center text-gray-600 text-sm">
                            Generated on {{ now.strftime('%Y-%m-%d %H:%M UTC') }}
                        </p>
                    </div>
                </footer>
            </body>
            </html>
            """
            
            template = Template(template_str)
            html_content = template.render(
                week_start=self.week_start,
                week_end=self.week_end,
                high_impact_updates=high_impact_updates,
                categorized_updates=categorized_updates,
                now=datetime.now(pytz.UTC)
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
        logging.info("DevOps News Aggregator completed successfully")
