# run_aggregator.py
import os
from src.logger import setup_logging
from src.aggregator.config_loader import load_config
from src.aggregator.news_aggregator import NewsAggregator
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

    # Generate outputs with raw entries
    generate_html(
        entries,
        aggregator.current_week_range,
        "Raw updates from various sources",  # Simple summary
        [],  # No action items for now
        []   # No additional resources for now
    )
    generate_rss(entries, aggregator.current_week_range)

    logger.info("DevOps Platform Updates Aggregator completed successfully.")

if __name__ == "__main__":
    main()
