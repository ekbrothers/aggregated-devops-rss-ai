# src/output/html_generator.py
from jinja2 import Environment, FileSystemLoader
import os
import logging
from src.utils.icon_mapping import ICON_MAPPING

def generate_html(entries, week_range, executive_summary, action_items, additional_resources, template_path='newsletter_template.html', output_dir='dist'):
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Organize entries by platform
        platforms = {}
        for entry in entries:
            platform_name = entry.get('provider_name', 'unknown')
            icon_slug = ICON_MAPPING.get(platform_name.lower(), 'question')  # Default to 'question' icon
            platform_url = f"https://simpleicons.org/icons/{icon_slug}.svg"
            
            if platform_name not in platforms:
                platforms[platform_name] = {
                    "entries": [],
                    "icon_url": platform_url
                }
            platforms[platform_name]["entries"].append({
                "title": entry.get('title', 'No Title'),
                "link": entry.get('link', '#'),
                "summary": entry['analysis'].get('summary', "No summary available."),
                "impact_level": entry['analysis'].get('impact_level', 'LOW'),
                "key_changes": entry['analysis'].get('key_changes', []),
                "action_items": entry['analysis'].get('action_items', [])
            })
        
        # Setup Jinja2 environment
        env = Environment(loader=FileSystemLoader(searchpath='./'))
        template = env.get_template(template_path)
        
        # Prepare data for template
        start_date = week_range[0].strftime('%B %d, %Y')
        end_date = week_range[1].strftime('%B %d, %Y')
        template_data = {
            'week_range': f"{start_date} - {end_date}",
            'platforms': platforms,
            'executive_summary': executive_summary,
            'action_items': action_items,
            'additional_resources': additional_resources
        }
        
        # Render HTML
        html_content = template.render(**template_data)
        output_path = os.path.join(output_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"HTML newsletter generated successfully at {output_path}")
    except Exception as e:
        logging.error(f"Error generating HTML newsletter: {e}")
