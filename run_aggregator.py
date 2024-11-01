# run_aggregator.py
import os
from src.logger import setup_logging
from src.aggregator.config_loader import load_config
from src.aggregator.news_aggregator import NewsAggregator
from src.analysis.analyze_with_claude import analyze_entry
from src.output import generate_html, generate_rss
import logging

def main():
    logger = setup_logging()
    logger.info("Starting DevOps Platform Updates Aggregator")

    # Load configuration
    config = load_config()

    # Initialize aggregator
    aggregator = NewsAggregator(config)
    entries = aggregator.aggregate()

    # Analyze entries with Claude AI
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set in environment variables.")
        return

    executive_summaries = []
    action_items = []
    additional_resources = []

    for entry in entries:
        content = entry.get('content', '')
        source = entry.get('provider_name', 'unknown')
        title = entry.get('title', 'Untitled')
        analysis = analyze_entry(content, source, title, api_key)
        entry['analysis'] = analysis

        # Collect executive summaries
        summary = analysis.get('summary')
        if summary and summary != "No summary available.":
            executive_summaries.append(summary)
            logger.debug(f"Collected summary for '{title}': {summary}")
        else:
            logger.warning(f"No summary available for entry '{title}'.")

        # Collect action items
        action = analysis.get('action_items')
        if action:
            action_items.extend(action)
            logger.debug(f"Collected action items for '{title}': {action}")

        # Collect additional resources
        # Customize this as needed
        additional_resources.append({
            'name': f"{source.capitalize()} Documentation",
            'link': entry.get('link', '#')
        })

    # Generate a consolidated executive summary using Claude AI
    consolidated_summary = generate_consolidated_summary(executive_summaries, api_key)
    logger.debug(f"Consolidated Executive Summary: {consolidated_summary}")

    # Remove duplicate action items
    unique_action_items = list(set(action_items))
    logger.debug(f"Unique Action Items: {unique_action_items}")

    # Remove duplicate additional resources
    unique_additional_resources = [dict(t) for t in {tuple(d.items()) for d in additional_resources}]
    logger.debug(f"Unique Additional Resources: {unique_additional_resources}")

    # Generate outputs
    generate_html(
        entries,
        aggregator.current_week_range,
        consolidated_summary,
        unique_action_items,
        unique_additional_resources
    )
    generate_rss(entries, aggregator.current_week_range)

    logger.info("DevOps Platform Updates Aggregator completed successfully.")

def generate_consolidated_summary(summaries, api_key):
    """
    Generates a consolidated executive summary from individual summaries using Claude AI.
    """
    if not summaries:
        logging.warning("No individual summaries available to generate an executive summary.")
        return "No executive summary available."

    prompt = f"""Consolidate the following summaries into a cohesive executive summary for a weekly DevOps update:

{chr(10).join(summaries)}

Provide the consolidated summary in 3-4 sentences."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key)
        response = client.completions.create(
            model="claude-v1",
            prompt=prompt,
            max_tokens=300,
            stop_sequences=["\n\n"]
        )
        consolidated_summary = response['completion'].strip()
        logging.info("Consolidated executive summary generated.")
        logging.debug(f"Consolidated Summary: {consolidated_summary}")
        return consolidated_summary
    except Exception as e:
        logging.error(f"Error generating consolidated summary: {e}")
        return "No executive summary available."

if __name__ == "__main__":
    main()
