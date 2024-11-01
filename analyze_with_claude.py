# analyze_with_claude.py
import json
import logging
from anthropic import Anthropic

def analyze_with_claude(content, source, title, api_key):
    """
    Analyze the given content using Claude AI and return structured analysis.

    Parameters:
        content (str): Content to be analyzed.
        source (str): The source of the update.
        title (str): The title of the update.
        api_key (str): API key for Claude AI.

    Returns:
        dict: JSON response containing summary, impact level, key changes, and more.
    """
    anthropic_client = Anthropic(api_key=api_key)
    
    prompt = f"""Analyze this DevOps update and provide an expanded, detailed summary, focusing on practical implications for DevOps teams.

Source: {source}
Title: {title}
Content: {content}

Provide response in JSON format with these fields:
1. summary: 3-5 sentence summary with detailed context
2. impact_level: HIGH/MEDIUM/LOW based on urgency for action
3. key_changes: List of 2-3 most important changes with explanation
4. action_items: List of specific actions DevOps teams should take
5. affected_services: List of impacted technologies/services
6. tags: List of relevant categories (SECURITY/FEATURE/PERFORMANCE/DEPRECATION)"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Try to decode JSON response and log if it fails
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from Claude API response: {response.content}")
            return {}
    except Exception as e:
        logging.error(f"Claude API analysis error: {str(e)}")
        return {}
