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
from jinja2 import Template

class DevOpsNewsAggregator:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.feeds = self._load_config()
        self.entries = []
        self.important_updates = []
        self.current_week_range = self._get_week_range()
        logging.basicConfig(level=logging.INFO)

    def _get_week_range(self):
        """Get the date range for the current week (Friday to Friday)"""
        today = datetime.now(pytz.UTC)
        # Find last Friday
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday)
        last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_friday = last_friday + timedelta(days=7)
        return last_friday, next_friday

    def _is_in_current_week(self, entry_date):
        """Check if an entry falls within the current week range"""
        if isinstance(entry_date, tuple):
            entry_date = datetime(*entry_date[:6], tzinfo=pytz.UTC)
        return self.current_week_range[0] <= entry_date < self.current_week_range[1]

    def analyze_with_claude(self, content: str, source: str, title: str) -> Dict:
        prompt = f"""Analyze this DevOps update and provide a concise summary. Focus on practical implications for DevOps teams.

Source: {source}
Title: {title}
Content: {content}

Provide response in JSON format with these fields:
1. summary: 2-3 sentence summary of key changes
2. impact_level: HIGH/MEDIUM/LOW based on how urgently teams should act
3. key_changes: List of 2-3 most important changes (bullet points)
4. action_items: List of specific actions DevOps teams should take
5. affected_services: List of related technologies/services impacted
6. tags: List of relevant categories (SECURITY/FEATURE/PERFORMANCE/DEPRECATION)"""

        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content)

    def generate_html_newsletter(self):
        try:
            os.makedirs('dist', exist_ok=True)
            
            # Group entries by impact level
            high_impact = []
            medium_impact = []
            low_impact = []
            
            for entry in self.entries:
                if not hasattr(entry, 'published_parsed'):
                    continue
                    
                entry_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                if not self._is_in_current_week(entry_date):
                    continue
                    
                analysis = entry.get('analysis', {})
                impact = analysis.get('impact_level', 'LOW')
                
                if impact == 'HIGH':
                    high_impact.append(entry)
                elif impact == 'MEDIUM':
                    medium_impact.append(entry)
                else:
                    low_impact.append(entry)

            # Get the week range for the title
            start_date = self.current_week_range[0].strftime('%B %d, %Y')
            end_date = self.current_week_range[1].strftime('%B %d, %Y')
            
            template_data = {
                'week_range': f"{start_date} - {end_date}",
                'high_impact': high_impact,
                'medium_impact': medium_impact,
                'low_impact': low_impact
            }

            with open('newsletter_template.html', 'r') as f:
                template = Template(f.read())
            
            html_content = template.render(**template_data)
            
            with open('dist/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logging.info("HTML newsletter generated successfully")
        except Exception as e:
            logging.error(f"Error generating HTML newsletter: {str(e)}")

    def run(self):
        self.fetch_rss_feeds()
        self.fetch_manual_sources()
        
        # Analyze entries with Claude
        for entry in self.entries:
            if hasattr(entry, 'published_parsed'):
                entry_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                if self._is_in_current_week(entry_date):
                    entry['analysis'] = self.analyze_with_claude(
                        entry.get('summary', ''), 
                        entry.get('provider_name', 'Unknown'),
                        entry.get('title', 'Untitled')
                    )
        
        self.generate_html_newsletter()
        self.generate_rss_feed()
        logging.info("DevOps News Aggregator completed successfully")
