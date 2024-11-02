import json
from datetime import datetime
from typing import Dict, List, Optional

def analyze_updates(updates: List[Dict]) -> Dict:
    """
    Analyze updates and generate structured data for the HTML template.
    """
    analyzed_data = {
        'date_range': _get_date_range(updates),
        'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updates_by_source': {},
        'executive_summary': '',
        'action_items': [],
        'breaking_changes_count': 0,
        'security_updates_count': 0,
        'new_features_count': 0,
        'total_updates_count': len(updates)
    }

    # Group updates by source
    for update in updates:
        source = update['source']
        if source not in analyzed_data['updates_by_source']:
            analyzed_data['updates_by_source'][source] = []
        
        # Analyze update content
        analyzed_update = _analyze_single_update(update)
        
        # Update counts
        if 'Breaking Change' in analyzed_update['categories']:
            analyzed_data['breaking_changes_count'] += 1
        if 'Security' in analyzed_update['categories']:
            analyzed_data['security_updates_count'] += 1
        if 'New Feature' in analyzed_update['categories']:
            analyzed_data['new_features_count'] += 1
            
        analyzed_data['updates_by_source'][source].append(analyzed_update)
        
        # Collect action items
        if analyzed_update['action_items']:
            analyzed_data['action_items'].extend(analyzed_update['action_items'])

    # Generate executive summary
    analyzed_data['executive_summary'] = _generate_executive_summary(analyzed_data)

    return analyzed_data

def _analyze_single_update(update: Dict) -> Dict:
    """
    Analyze a single update and structure its data.
    """
    # Determine impact level and categories
    impact, categories = _analyze_impact_and_categories(update['content'])
    
    # Extract key changes and action items
    key_changes = _extract_key_changes(update['content'])
    action_items = _extract_action_items(update['content'])
    
    # Generate summary
    summary = _generate_summary(update['content'])

    return {
        'title': update['title'],
        'url': update['url'],
        'date': update['date'],
        'impact': impact,
        'impact_class': f'impact-{impact.lower()}',
        'impact_badge_class': _get_impact_badge_class(impact),
        'categories': categories,
        'summary': summary,
        'key_changes': key_changes,
        'action_items': action_items
    }

def _analyze_impact_and_categories(content: str) -> tuple[str, List[str]]:
    """
    Analyze content to determine impact level and categories.
    Returns tuple of (impact_level, categories).
    """
    # Default values
    impact = 'Low'
    categories = []
    
    # Keywords indicating high impact
    high_impact_keywords = [
        'breaking change', 'critical', 'security vulnerability',
        'urgent', 'immediate action', 'major version'
    ]
    
    # Keywords indicating medium impact
    medium_impact_keywords = [
        'deprecation', 'upgrade recommended', 'performance improvement',
        'new feature', 'enhancement'
    ]
    
    # Category keywords
    category_keywords = {
        'Infrastructure': ['kubernetes', 'docker', 'infrastructure', 'helm'],
        'CI/CD': ['pipeline', 'ci/cd', 'continuous integration', 'deployment'],
        'Security': ['security', 'vulnerability', 'authentication', 'authorization'],
        'Cloud': ['aws', 'azure', 'gcp', 'cloud'],
        'Tools': ['tool', 'plugin', 'extension', 'utility'],
        'Breaking Change': ['breaking change', 'major version'],
        'New Feature': ['new feature', 'added', 'introduced'],
        'Performance': ['performance', 'optimization', 'speed'],
        'Documentation': ['documentation', 'docs', 'guide']
    }
    
    content_lower = content.lower()
    
    # Determine impact
    if any(keyword in content_lower for keyword in high_impact_keywords):
        impact = 'High'
    elif any(keyword in content_lower for keyword in medium_impact_keywords):
        impact = 'Medium'
    
    # Determine categories
    for category, keywords in category_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            categories.append(category)
    
    # Ensure at least one category
    if not categories:
        categories.append('General')
    
    return impact, categories

def _extract_key_changes(content: str) -> List[str]:
    """
    Extract key changes from content.
    """
    # This is a simplified version - in practice, you'd want to use more sophisticated
    # NLP techniques to extract meaningful changes
    changes = []
    
    # Split content into sentences and look for relevant ones
    sentences = content.split('. ')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in [
            'added', 'removed', 'updated', 'changed', 'fixed', 'improved',
            'deprecated', 'introduced'
        ]):
            changes.append(sentence.strip() + '.')
    
    return changes[:5]  # Limit to top 5 changes

def _extract_action_items(content: str) -> List[str]:
    """
    Extract action items from content.
    """
    # This is a simplified version - in practice, you'd want to use more sophisticated
    # NLP techniques to extract actionable items
    actions = []
    
    # Split content into sentences and look for relevant ones
    sentences = content.split('. ')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in [
            'required', 'must', 'should', 'need to', 'recommended',
            'please update', 'ensure', 'upgrade to'
        ]):
            actions.append(sentence.strip() + '.')
    
    return actions

def _generate_summary(content: str) -> str:
    """
    Generate a concise summary of the content.
    """
    # This is a simplified version - in practice, you'd want to use more sophisticated
    # NLP techniques to generate summaries
    sentences = content.split('. ')
    summary = '. '.join(sentences[:3]) + '.'
    return summary

def _generate_executive_summary(data: Dict) -> str:
    """
    Generate an executive summary based on the analyzed data.
    """
    summary_parts = []
    
    # Overview
    summary_parts.append(f"This week's update includes {data['total_updates_count']} changes across various DevOps tools and platforms.")
    
    # Highlight significant changes
    if data['breaking_changes_count'] > 0:
        summary_parts.append(f"There are {data['breaking_changes_count']} breaking changes that require immediate attention.")
    
    if data['security_updates_count'] > 0:
        summary_parts.append(f"There are {data['security_updates_count']} security-related updates.")
    
    if data['new_features_count'] > 0:
        summary_parts.append(f"There are {data['new_features_count']} new features or enhancements.")
    
    # Action items summary
    if data['action_items']:
        summary_parts.append(f"There are {len(data['action_items'])} action items that require review.")
    
    return ' '.join(summary_parts)

def _get_date_range(updates: List[Dict]) -> str:
    """
    Get the date range for the updates.
    """
    dates = [datetime.strptime(update['date'], '%Y-%m-%d') for update in updates]
    start_date = min(dates)
    end_date = max(dates)
    return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

def _get_impact_badge_class(impact: str) -> str:
    """
    Get the CSS class for impact badge.
    """
    return {
        'High': 'bg-red-500',
        'Medium': 'bg-yellow-500',
        'Low': 'bg-green-500'
    }.get(impact, 'bg-blue-500')
