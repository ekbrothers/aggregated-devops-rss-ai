# src/logger.py
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger()
