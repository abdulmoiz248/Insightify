"""Configuration loader utility."""

import yaml
import os
from pathlib import Path


def load_config(config_path: str = None):
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If not provided, searches for config/config.yml
                     relative to the project root.
    
    Returns:
        Dictionary containing configuration
    """
    if config_path is None:
        # Find project root (where config directory exists)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent  # Go up to project root from utils/
        config_path = project_root / 'config' / 'config.yml'
    else:
        config_path = Path(config_path)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
