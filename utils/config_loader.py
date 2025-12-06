"""Configuration loader utility."""

import yaml
import os


def load_config(config_path: str = 'config/config.yml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
