from jinja2 import Environment, FileSystemLoader
import os
import logging
import shutil
from datetime import datetime
from src.utils.icon_mapping import ICON_MAPPING

def generate_html(entries, week_range, executive_summary, action_items, additional_resources, template_path='newsletter_template.html', output_dir='dist'):
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
        
        # Process entries and organize by type and source
        updates_by_type = {}
        stats = {
            'breaking_changes_count': 0,
            'security_updates_count': 0,
            'new_features_count': 0,
            'total_updates_count': len(entries)
        }
        
        for entry in entries:
            source_type = entry.get('source_type', 'other')
            provider_name = entry.get('provider_name', 'unknown')
            
            # Initialize source type if not exists
            if source_type not in updates_by_type:
                updates_by_type[source_type] = {}
            
            # Initialize provider if not exists
            if provider_name not in updates_by_type[source_type]:
                updates_by_type[source_type][provider_name] = {
                    'name': provider_name.title(),
                    'icon': ICON_MAPPING.get(provider_name, 'question.svg'),
                    'entries': []
                }
            
            # Process entry
            processed_entry = {
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', '#'),
                'published': entry.get('published', ''),
                'content': entry.get('content', 'No content available.'),
                'impact': 'LOW',  # Default impact
                'impact_class': 'impact-low',
                'impact_badge_class': 'bg-green-500',
                'categories': ['General'],
                'key_changes': []
            }
            
            # Update statistics based on content
            content_lower = processed_entry['content'].lower()
            if 'breaking' in content_lower or 'critical' in content_lower:
                stats['breaking_changes_count'] += 1
                processed_entry['impact'] = 'HIGH'
                processed_entry['impact_class'] = 'impact-high'
                processed_entry['impact_badge_class'] = 'bg-red-500'
                processed_entry['categories'].append('Breaking Change')
            
            if 'security' in content_lower or 'vulnerability' in content_lower:
                stats['security_updates_count'] += 1
                processed_entry['categories'].append('Security')
            
            if 'new' in content_lower or 'feature' in content_lower:
                stats['new_features_count'] += 1
                processed_entry['categories'].append('New Feature')
            
            # Add source-specific categories
            if source_type == 'terraform_providers':
                processed_entry['categories'].append('Infrastructure')
            elif source_type == 'vcs_platforms':
                processed_entry['categories'].append('CI/CD')
            elif source_type == 'ai_tools':
                processed_entry['categories'].append('AI/ML')
            elif source_type == 'cloud_providers':
                processed_entry['categories'].append('Cloud')
            
            # Remove duplicates and sort categories
            processed_entry['categories'] = sorted(list(set(processed_entry['categories'])))
            
            # Extract key changes
            key_changes = []
            for sentence in content_lower.split('. '):
                if any(keyword in sentence for keyword in ['add', 'new', 'fix', 'update', 'improve', 'change']):
                    key_changes.append(sentence.strip() + '.')
            processed_entry['key_changes'] = key_changes[:5]  # Limit to top 5 changes
            
            # Add to updates
            updates_by_type[source_type][provider_name]['entries'].append(processed_entry)

        # Setup Jinja2 environment
        env = Environment(loader=FileSystemLoader(searchpath='./'))
        template = env.get_template(template_path)
        
        # Prepare template data
        template_data = {
            'date_range': f"{week_range[0].strftime('%B %d, %Y')} - {week_range[1].strftime('%B %d, %Y')}",
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updates_by_type': updates_by_type,
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

def _get_impact_badge_class(impact):
    """
    Get the CSS class for impact badge.
    """
    return {
        'HIGH': 'bg-red-500',
        'MEDIUM': 'bg-yellow-500',
        'LOW': 'bg-green-500'
    }.get(impact, 'bg-blue-500')
