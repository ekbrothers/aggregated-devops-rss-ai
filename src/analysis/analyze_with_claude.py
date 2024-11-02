# src/analysis/analyze_with_claude.py
import json
import logging
from anthropic import Anthropic

def analyze_entry(content, source, title, api_key):
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
{{
  "summary": "This release introduces critical updates...",
  "impact_level": "HIGH",
  "key_changes": ["New feature X improves...", "Performance enhancements..."],
  "action_items": ["Update to the latest version...", "Review new configuration options..."],
  "affected_services": ["AWS", "Terraform"]
}}"""

    try:
        client = Anthropic(api_key)
        response = client.completions.create(
            model="claude-v1",
            prompt=prompt,
            max_tokens=500,
            stop_sequences=["}"]
        )
        response_text = response['completion'].strip()
        
        # Ensure the JSON is properly closed
        if not response_text.endswith('}'):
            response_text += "}"
        
        logging.debug(f"Claude AI raw response for '{title}': {response_text}")
        
        # Attempt to parse the JSON
        analysis = json.loads(response_text)
        logging.info(f"Analyzed entry: {title} - Impact level: {analysis.get('impact_level', 'None')}")
        return analysis
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error for entry '{title}': {e}")
        logging.error(f"Response Text: {response_text}")
        return {
            "summary": "No summary available.",
            "impact_level": "LOW",
            "key_changes": [],
            "action_items": [],
            "affected_services": []
        }
    except Exception as e:
        logging.error(f"Error analyzing entry '{title}': {e}")
        return {
            "summary": "No summary available.",
            "impact_level": "LOW",
            "key_changes": [],
            "action_items": [],
            "affected_services": []
        }
