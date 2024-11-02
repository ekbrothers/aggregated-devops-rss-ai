# src/output/html_generator.py
from jinja2 import Environment, FileSystemLoader
import os
import logging
from src.utils.icon_mapping import ICON_MAPPING

def generate_html(entries, week_range, executive_summary, action_items, additional_resources, template_path='newsletter_template.html', output_dir='dist'):
    try:
        # Create necessary directories
        os.makedirs(os.path.join(output_dir, 'assets/icons'), exist_ok=True)
        
        # Copy local icons to the output directory
        for icon_file in ICON_MAPPING.values():
            source_path = os.path.join('assets', 'icons', icon_file)
            dest_path = os.path.join(output_dir, 'assets', 'icons', icon_file)
            if os.path.exists(source_path):
                with open(source_path, 'r', encoding='utf-8') as src, open(dest_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logging.debug(f"Copied {source_path} to {dest_path}")
            else:
                logging.error(f"Icon file {source_path} does not exist.")
        
        # Organize entries by platform
        platforms = {}
        for entry in entries:
            platform_name = entry.get('provider_name', 'unknown').lower()
            icon_filename = ICON_MAPPING.get(platform_name, 'question.svg')  # Default to 'question.svg'
            icon_path = f"assets/icons/{icon_filename}"
            
            # Log the mapping
            logging.debug(f"Mapping provider '{platform_name}' to icon '{icon_path}'")
            
            if platform_name not in platforms:
                platforms[platform_name] = {
                    "entries": [],
                    "icon_url": icon_path
                }
            platforms[platform_name]["entries"].append({
                "title": entry.get('title', 'No Title'),
                "link": entry.get('link', '#'),
                "summary": entry['analysis'].get('summary', "No summary available."),
                "impact_level": entry['analysis'].get('impact_level', 'LOW'),
                "key_changes": entry['analysis'].get('key_changes', []),
                "action_items": entry['analysis'].get('action_items', [])
            })
        
        # Remove 'unknown' platform if not desired
        if 'unknown' in platforms:
            logging.warning("Some entries have an unknown provider. These entries will be excluded from the Key Highlights.")
            del platforms['unknown']

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
