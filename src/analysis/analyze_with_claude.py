import json
import logging
from anthropic import Anthropic
from datetime import datetime
from typing import Dict, List

def analyze_entry(content: str, source: str, title: str, api_key: str) -> Dict:
    """
    Analyze a single entry using Claude AI.
    """
    example_response = {
        "summary": "This release introduces critical updates...",
        "impact_level": "HIGH",
        "key_changes": ["New feature X improves...", "Performance enhancements..."],
        "action_items": ["Update to the latest version...", "Review new configuration options..."],
        "affected_services": ["AWS", "Terraform"]
    }

    prompt = f"""Analyze this DevOps update and provide a comprehensive summary, focusing on critical information for DevOps engineers.

Source: {source}
Title: {title}
Content: {content}

Provide your response in JSON format with these fields:
1. summary: A 3-5 sentence summary explaining the core update.
2. impact_level: HIGH, MEDIUM, or LOW depending on the urgency for DevOps teams to act.
3. key_changes: A list of 2-3 main changes or new features.
4. action_items: Actionable points that DevOps teams should consider.
5. affected_services: Any relevant tools or platforms impacted.

Example response:
{json.dumps(example_response, indent=2)}"""

    try:
        client = Anthropic(api_key)
        response = client.completions.create(
            model="claude-v1",
            prompt=prompt,
            max_tokens=500,
            stop_sequences=["}"]
        )
        response_text = response.completion.strip()
        
        # Ensure the JSON is properly closed
        if not response_text.endswith('}'):
            response_text += "}"
        
        logging.debug(f"Claude AI raw response for '{title}': {response_text}")
        
        try:
            # Parse the JSON response
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['summary', 'impact_level', 'key_changes', 'action_items', 'affected_services']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = [] if field in ['key_changes', 'action_items', 'affected_services'] else ''
            
            # Ensure all fields are strings or lists
            analysis['summary'] = str(analysis.get('summary', ''))
            analysis['impact_level'] = str(analysis.get('impact_level', 'LOW')).upper()
            analysis['key_changes'] = [str(change) for change in analysis.get('key_changes', [])]
            analysis['action_items'] = [str(item) for item in analysis.get('action_items', [])]
            analysis['affected_services'] = [str(service) for service in analysis.get('affected_services', [])]
            
            # Enhance the analysis with additional processing
            enhanced_analysis = _enhance_analysis(analysis, title, content)
            
            logging.info(f"Analyzed entry: {title} - Impact level: {enhanced_analysis.get('impact_level', 'None')}")
            return enhanced_analysis
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for entry '{title}': {e}")
            logging.error(f"Response Text: {response_text}")
            return _get_default_analysis()
            
    except Exception as e:
        logging.error(f"Error analyzing entry '{title}': {e}")
        return _get_default_analysis()

def _enhance_analysis(analysis: Dict, title: str, content: str) -> Dict:
    """
    Enhance the basic analysis with additional processing.
    """
    # Determine impact level and categories
    impact_level = analysis.get('impact_level', 'LOW')
    categories = _determine_categories(analysis, content)
    
    # Extract key changes if none provided
    key_changes = analysis.get('key_changes', [])
    if not key_changes:
        key_changes = _extract_key_changes(content)
    
    # Extract action items if none provided
    action_items = analysis.get('action_items', [])
    if not action_items:
        action_items = _extract_action_items(content)
    
    return {
        'summary': str(analysis.get('summary', 'No summary available.')),
        'impact_level': str(impact_level).upper(),
        'key_changes': [str(change) for change in key_changes],
        'action_items': [str(item) for item in action_items],
        'affected_services': [str(service) for service in analysis.get('affected_services', [])],
        'categories': categories
    }

def _determine_categories(analysis: Dict, content: str) -> List[str]:
    """
    Determine categories based on analysis content.
    """
    categories = set()
    content_lower = content.lower()
    
    # Add categories based on affected services
    for service in analysis.get('affected_services', []):
        service_lower = str(service).lower()
        if service_lower in ['aws', 'azure', 'gcp']:
            categories.add('Cloud')
        elif service_lower in ['kubernetes', 'docker']:
            categories.add('Infrastructure')
        elif service_lower in ['jenkins', 'gitlab', 'github']:
            categories.add('CI/CD')
    
    # Add categories based on impact and content
    impact = str(analysis.get('impact_level', '')).upper()
    if impact == 'HIGH':
        categories.add('Breaking Change')
    
    # Look for security-related content
    if any(word in content_lower for word in ['security', 'vulnerability', 'cve']):
        categories.add('Security')
    
    # Look for new features
    if any(str(change).lower().startswith(('add', 'new', 'introduce')) 
           for change in analysis.get('key_changes', [])):
        categories.add('New Feature')
    
    # Ensure at least one category
    if not categories:
        categories.add('General')
    
    return sorted(list(categories))

def _extract_key_changes(content: str) -> List[str]:
    """
    Extract key changes from content.
    """
    changes = []
    sentences = content.split('. ')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in [
            'added', 'removed', 'updated', 'changed', 'fixed', 'improved',
            'deprecated', 'introduced'
        ]):
            changes.append(str(sentence).strip() + '.')
    
    return changes[:5]  # Limit to top 5 changes

def _extract_action_items(content: str) -> List[str]:
    """
    Extract action items from content.
    """
    actions = []
    sentences = content.split('. ')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in [
            'required', 'must', 'should', 'need to', 'recommended',
            'please update', 'ensure', 'upgrade to'
        ]):
            actions.append(str(sentence).strip() + '.')
    
    return actions

def _get_default_analysis() -> Dict:
    """
    Get default analysis structure for error cases.
    """
    return {
        'summary': 'No summary available.',
        'impact_level': 'LOW',
        'key_changes': [],
        'action_items': [],
        'affected_services': [],
        'categories': ['General']
    }
