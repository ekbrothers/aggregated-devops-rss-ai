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

    for entry in entries:
        content = entry.get('content', '')
        source = entry.get('provider_name', 'Unknown Platform')
        title = entry.get('title', 'Untitled')
        entry['analysis'] = analyze_entry(content, source, title, api_key)

    # Generate outputs
    generate_html(entries, aggregator.current_week_range)
    generate_rss(entries, aggregator.current_week_range)

    logger.info("DevOps Platform Updates Aggregator completed successfully.")

if __name__ == "__main__":
    main()
