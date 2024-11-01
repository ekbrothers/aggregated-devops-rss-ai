# analyze_with_claude.py
import json
import logging
from anthropic import Anthropic

def analyze_with_claude(content, source, title, api_key):
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
    # Call Claude API with prompt, parse, and return JSON response.
    response = {"summary": "Sample summary...", "impact_level": "MEDIUM", "key_changes": ["Example"], "action_items": ["Do this"]}
    return response
