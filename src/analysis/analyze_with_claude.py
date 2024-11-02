import json
import logging
from anthropic import Anthropic
from datetime import datetime
from typing import Dict, List

def analyze_entry(content: str, source: str, title: str, api_key: str, source_type: str = None, source_metadata: Dict = None) -> Dict:
    """
    Analyze a single entry using Claude AI.
    """
    # Create source-specific prompt
    prompt = _create_source_specific_prompt(content, source, title, source_type, source_metadata)

    try:
        client = Anthropic(api_key)
        response = client.completions.create(
            model="claude-v1",
            prompt=prompt,
            max_tokens=1000,
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
            
            # Enhance the analysis with source-specific processing
            enhanced_analysis = _enhance_analysis(analysis, title, content, source_type, source_metadata)
            
            logging.info(f"Analyzed entry: {title} - Impact level: {enhanced_analysis.get('impact_level', 'None')}")
            return enhanced_analysis
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for entry '{title}': {e}")
            logging.error(f"Response Text: {response_text}")
            return _get_default_analysis(source_type)
            
    except Exception as e:
        logging.error(f"Error analyzing entry '{title}': {e}")
        return _get_default_analysis(source_type)

def _create_source_specific_prompt(content: str, source: str, title: str, source_type: str, source_metadata: Dict) -> str:
    """
    Create a source-specific prompt based on the type of source.
    """
    base_prompt = f"""Analyze this DevOps update and provide a comprehensive summary, focusing on critical information for DevOps engineers.

Source: {source}
Title: {title}
Type: {source_type}
Content: {content}
"""

    if source_type == "terraform_providers":
        prompt_addition = """
Focus on:
1. Breaking changes in provider behavior
2. New resources or data sources
3. Bug fixes that might affect existing infrastructure
4. Required provider version changes
5. Deprecated features or resources"""

    elif source_type == "vcs_platforms":
        prompt_addition = """
Focus on:
1. New features for CI/CD pipelines
2. Security updates or requirements
3. API changes or deprecations
4. Performance improvements
5. Integration capabilities"""

    elif source_type == "ai_tools":
        prompt_addition = """
Focus on:
1. New capabilities or models
2. Performance improvements
3. API changes
4. Integration features
5. Security or compliance updates"""

    elif source_type == "devops_tools":
        prompt_addition = """
Focus on:
1. Security implications
2. Breaking changes
3. New features or capabilities
4. Performance improvements
5. Integration updates"""
    else:
        prompt_addition = ""

    response_format = """
Provide your response in JSON format with these fields:
1. summary: A 3-5 sentence summary explaining the core update.
2. impact_level: HIGH, MEDIUM, or LOW depending on the urgency for DevOps teams to act.
3. key_changes: A list of main changes or new features.
4. action_items: Actionable points that DevOps teams should consider.
5. affected_services: Any relevant tools or platforms impacted.
6. breaking_changes: List of breaking changes (if any).
7. security_updates: List of security-related updates (if any).
8. deprecations: List of deprecated features (if any).
9. new_features: List of new features or enhancements.
10. platform_status: Current platform status (for VCS platforms).

Example response:
{
    "summary": "This release introduces critical updates...",
    "impact_level": "HIGH",
    "key_changes": ["New feature X improves...", "Performance enhancements..."],
    "action_items": ["Update to the latest version...", "Review new configuration options..."],
    "affected_services": ["AWS", "Terraform"],
    "breaking_changes": ["API endpoint X deprecated..."],
    "security_updates": ["Fixed vulnerability in..."],
    "deprecations": ["Feature Y will be removed..."],
    "new_features": ["Added support for..."],
    "platform_status": "Operational"
}"""

    return base_prompt + prompt_addition + response_format

def _enhance_analysis(analysis: Dict, title: str, content: str, source_type: str, source_metadata: Dict) -> Dict:
    """
    Enhance the basic analysis with source-specific processing.
    """
    # Ensure all fields exist with proper types
    enhanced = {
        'summary': str(analysis.get('summary', 'No summary available.')),
        'impact_level': str(analysis.get('impact_level', 'LOW')).upper(),
        'key_changes': [str(change) for change in analysis.get('key_changes', [])],
        'action_items': [str(item) for item in analysis.get('action_items', [])],
        'affected_services': [str(service) for service in analysis.get('affected_services', [])],
        'breaking_changes': [str(change) for change in analysis.get('breaking_changes', [])],
        'security_updates': [str(update) for update in analysis.get('security_updates', [])],
        'deprecations': [str(dep) for dep in analysis.get('deprecations', [])],
        'new_features': [str(feature) for feature in analysis.get('new_features', [])],
        'platform_status': str(analysis.get('platform_status', 'Unknown')),
        'categories': _determine_categories(analysis, content, source_type),
        'source_type': source_type,
        'source_metadata': source_metadata or {}
    }

    # Add source-specific enhancements
    if source_type == "vcs_platforms" and source_metadata.get('status_url'):
        enhanced['status_url'] = source_metadata['status_url']

    return enhanced

def _determine_categories(analysis: Dict, content: str, source_type: str) -> List[str]:
    """
    Determine categories based on analysis content and source type.
    """
    categories = set()
    content_lower = content.lower()
    
    # Add source type as a category
    if source_type:
        categories.add(source_type.replace('_', ' ').title())

    # Add categories based on content
    if analysis.get('breaking_changes'):
        categories.add('Breaking Change')
    
    if analysis.get('security_updates'):
        categories.add('Security')
    
    if analysis.get('new_features'):
        categories.add('New Feature')

    if 'performance' in content_lower or 'optimization' in content_lower:
        categories.add('Performance')

    if 'api' in content_lower:
        categories.add('API')

    if 'deprecat' in content_lower:
        categories.add('Deprecation')

    # Source-specific categories
    if source_type == "terraform_providers":
        categories.add('Infrastructure')
    elif source_type == "vcs_platforms":
        categories.add('CI/CD')
    elif source_type == "ai_tools":
        categories.add('AI/ML')
    
    return sorted(list(categories))

def _get_default_analysis(source_type: str = None) -> Dict:
    """
    Get default analysis structure for error cases.
    """
    return {
        'summary': 'No summary available.',
        'impact_level': 'LOW',
        'key_changes': [],
        'action_items': [],
        'affected_services': [],
        'breaking_changes': [],
        'security_updates': [],
        'deprecations': [],
        'new_features': [],
        'platform_status': 'Unknown',
        'categories': [source_type.replace('_', ' ').title()] if source_type else ['General'],
        'source_type': source_type or 'unknown',
        'source_metadata': {}
    }
