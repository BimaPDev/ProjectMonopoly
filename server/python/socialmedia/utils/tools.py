import json
import os
from typing import Dict, Any

def read_settings() -> Dict[str, Any]:
    """Read settings from config file or return defaults."""
    default_settings = {
        "gral": {
            "headless": True
        },
        "instagram": {
            "time_ms": 6000,
            "max_posts": 5
        }
    }
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read settings file: {e}")
    
    return default_settings 