# src/aggregator/config_loader.py
import yaml
import logging

def load_config(config_path='config.yml'):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise
