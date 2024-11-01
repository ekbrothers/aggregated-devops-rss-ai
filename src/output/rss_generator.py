# src/output/rss_generator.py
import feedgenerator
import os
from datetime import datetime
import logging

def generate_rss(entries, week_range, output_dir='dist'):
    try:
        os.makedirs(output_dir, exist_ok=True)
        rss = feedgenerator.Rss201rev2Feed(
            title="DevOps Updates Digest",
            link="https://yourusername.github.io/yourrepo/",  # Update with your GitHub Pages URL
            description=f"Weekly digest of DevOps platform updates from {week_range[0].strftime('%B %d, %Y')} to {week_range[1].strftime('%B %d, %Y')}",
            language="en"
        )
        
        for entry in entries:
            rss.add_item(
                title=entry.get('title', 'No Title'),
                link=entry.get('link', '#'),
                description=entry['analysis'].get('summary', 'No summary available.'),
                pubdate=entry.get('published_parsed')
            )
        
        output_path = os.path.join(output_dir, 'feed.xml')
        with open(output_path, 'w', encoding='utf-8') as f:
            rss.write(f, 'utf-8')
        
        logging.info(f"RSS feed generated successfully at {output_path}")
    except Exception as e:
        logging.error(f"Error generating RSS feed: {e}")
