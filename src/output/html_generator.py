from jinja2 import Environment, FileSystemLoader
import os
import logging
import shutil
from datetime import datetime
import markdown
from src.utils.icon_mapping import ICON_MAPPING

def generate_html(entries, week_range, executive_summary, action_items, additional_resources, template_path='src/templates/base.html', output_dir='dist'):
    """
    Generate HTML newsletter from analyzed entries.
    """
    try:
        # Create necessary directories
        os.makedirs(os.path.join(output_dir, 'assets/icons'), exist_ok=True)
        
        # Copy local icons to the output directory
        for icon_file in ICON_MAPPING.values():
            source_path = os.path.join('src', 'assets', 'icons', icon_file)
            dest_path = os.path.join(output_dir, 'assets', 'icons', icon_file)
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                logging.debug(f"Copied {source_path} to {dest_path}")
            else:
                logging.error(f"Icon file {source_path} does not exist.")
        
        # Initialize markdown converter with code highlighting
        md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'tables'])
        
        # Process entries and organize by platform
        platforms = {}
        stats = {
            'breaking_changes_count': 0,
            'security_updates_count': 0,
            'new_features_count': 0,
            'total_updates_count': len(entries)
        }
        
        for entry in entries:
            platform_name = entry.get('provider_name', 'unknown').lower()
            source_name = entry.get('source_name', platform_name.title())
            icon_filename = ICON_MAPPING.get(platform_name, 'question.svg')
            icon_path = f"assets/icons/{icon_filename}"
            
            if platform_name not in platforms:
                platforms[platform_name] = {
                    "name": source_name,  # Use source_name from config.yml
                    "icon": icon_path,
                    "entries": []
                }
            
            # Process entry
            content = str(entry.get('content', 'No content available.'))
            content_type = entry.get('content_type', 'html')
            
            # Convert markdown to HTML if content is markdown
            if content_type == 'markdown':
                content = md.convert(content)
            
            # Get Claude's analysis
            analysis = entry.get('analysis', {})
            
            processed_entry = {
                "title": str(entry.get('title', 'No Title')),
                "url": str(entry.get('link', '#')),
                "published": str(entry.get('published', '')),
                "content": content,
                "content_type": content_type,
                "impact": analysis.get('impact_level', 'LOW').upper(),
                "impact_badge_class": {
                    'HIGH': 'bg-red-500',
                    'MEDIUM': 'bg-yellow-500',
                    'LOW': 'bg-green-500'
                }.get(analysis.get('impact_level', 'LOW').upper(), 'bg-green-500'),
                "categories": analysis.get('categories', ["General"]),
                "key_changes": analysis.get('key_changes', []),
                "breaking_changes": analysis.get('breaking_changes', []),
                "security_updates": analysis.get('security_updates', []),
                "new_features": analysis.get('new_features', []),
                "deprecations": analysis.get('deprecations', []),
                "action_items": analysis.get('action_items', []),
                "affected_services": analysis.get('affected_services', []),
                "platform_status": analysis.get('platform_status', 'Unknown'),
                "summary": analysis.get('summary', '')
            }
            
            # Update statistics based on Claude's analysis
            if processed_entry['breaking_changes']:
                stats['breaking_changes_count'] += 1
            if processed_entry['security_updates']:
                stats['security_updates_count'] += 1
            if processed_entry['new_features']:
                stats['new_features_count'] += 1
            
            # Add to platforms
            platforms[platform_name]["entries"].append(processed_entry)
        
        # Remove 'unknown' platform if present
        if 'unknown' in platforms:
            logging.warning("Some entries have an unknown provider. These entries will be excluded.")
            del platforms['unknown']

        # Setup Jinja2 environment with correct template directory
        template_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get src directory
        env = Environment(loader=FileSystemLoader(os.path.join(template_dir, 'templates')))
        
        # Add safe filter to allow HTML in content
        env.filters['safe'] = lambda x: x
        
        template = env.get_template('base.html')  # Now we can use relative path
        
        # Prepare template data
        template_data = {
            'date_range': f"{week_range[0].strftime('%B %d, %Y')} - {week_range[1].strftime('%B %d, %Y')}",
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updates_by_source': platforms,
            'breaking_changes_count': stats['breaking_changes_count'],
            'security_updates_count': stats['security_updates_count'],
            'new_features_count': stats['new_features_count'],
            'total_updates_count': stats['total_updates_count']
        }
        
        # Render HTML
        html_content = template.render(**template_data)
        output_path = os.path.join(output_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"HTML newsletter generated successfully at {output_path}")
        
    except Exception as e:
        logging.error(f"Error generating HTML newsletter: {e}")
        raise
