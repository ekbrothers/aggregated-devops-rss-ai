from jinja2 import Environment, FileSystemLoader
import os
import logging
import shutil
from src.utils.icon_mapping import ICON_MAPPING

def generate_html(entries, week_range, executive_summary, action_items, additional_resources, template_path='newsletter_template.html', output_dir='dist'):
    """
    Generate HTML newsletter from analyzed entries.
    
    Args:
        entries: List of analyzed entries
        week_range: Tuple of (start_date, end_date)
        executive_summary: Executive summary text
        action_items: List of action items
        additional_resources: List of additional resources
        template_path: Path to the HTML template
        output_dir: Output directory for the generated files
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
            icon_filename = ICON_MAPPING.get(platform_name, 'question.svg')
            icon_path = f"assets/icons/{icon_filename}"
            
            logging.debug(f"Mapping provider '{platform_name}' to icon '{icon_path}'")
            
            if platform_name not in platforms:
                platforms[platform_name] = {
                    "name": platform_name.title(),
                    "icon": icon_path,
                    "entries": []
                }
            
            # Process entry analysis
            analysis = entry['analysis']
            impact_level = analysis.get('impact_level', 'LOW').upper()
            categories = _determine_categories(analysis)
            
            # Update statistics
            if 'Breaking Change' in categories:
                stats['breaking_changes_count'] += 1
            if 'Security' in categories:
                stats['security_updates_count'] += 1
            if 'New Feature' in categories:
                stats['new_features_count'] += 1
            
            # Create processed entry
            processed_entry = {
                "title": entry.get('title', 'No Title'),
                "url": entry.get('link', '#'),
                "date": entry.get('published', ''),
                "summary": analysis.get('summary', "No summary available."),
                "impact": impact_level,
                "impact_class": f"impact-{impact_level.lower()}",
                "impact_badge_class": _get_impact_badge_class(impact_level),
                "categories": categories,
                "key_changes": analysis.get('key_changes', []),
                "action_items": analysis.get('action_items', [])
            }
            
            platforms[platform_name]["entries"].append(processed_entry)
        
        # Remove 'unknown' platform if present
        if 'unknown' in platforms:
            logging.warning("Some entries have an unknown provider. These entries will be excluded.")
            del platforms['unknown']

        # Setup Jinja2 environment
        env = Environment(loader=FileSystemLoader(searchpath='./'))
        template = env.get_template(template_path)
        
        # Prepare template data
        template_data = {
            'date_range': f"{week_range[0].strftime('%B %d, %Y')} - {week_range[1].strftime('%B %d, %Y')}",
            'generation_date': week_range[1].strftime('%Y-%m-%d %H:%M:%S'),
            'updates_by_source': platforms,
            'executive_summary': executive_summary,
            'action_items': action_items,
            'additional_resources': additional_resources,
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

def _determine_categories(analysis):
    """
    Determine categories based on analysis content.
    """
    categories = set()
    
    # Add categories based on affected services
    if 'affected_services' in analysis:
        for service in analysis['affected_services']:
            if service.lower() in ['aws', 'azure', 'gcp']:
                categories.add('Cloud')
            elif service.lower() in ['kubernetes', 'docker']:
                categories.add('Infrastructure')
            elif service.lower() in ['jenkins', 'gitlab', 'github']:
                categories.add('CI/CD')
    
    # Add categories based on impact and content
    impact = analysis.get('impact_level', '').upper()
    if impact == 'HIGH':
        categories.add('Breaking Change')
    
    # Look for security-related content
    summary = analysis.get('summary', '').lower()
    if any(word in summary for word in ['security', 'vulnerability', 'cve']):
        categories.add('Security')
    
    # Look for new features
    if any(change.lower().startswith(('add', 'new', 'introduce')) 
           for change in analysis.get('key_changes', [])):
        categories.add('New Feature')
    
    # Ensure at least one category
    if not categories:
        categories.add('General')
    
    return sorted(list(categories))

def _get_impact_badge_class(impact):
    """
    Get the CSS class for impact badge.
    """
    return {
        'HIGH': 'bg-red-500',
        'MEDIUM': 'bg-yellow-500',
        'LOW': 'bg-green-500'
    }.get(impact, 'bg-blue-500')
