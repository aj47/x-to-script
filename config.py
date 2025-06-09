"""
Configuration settings for the x-thread-dl tool.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Apify API token
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Default settings
DEFAULT_REPLY_LIMIT = 50
DEFAULT_OUTPUT_DIR = "output"  # Base directory for all downloaded content

# Apify actor IDs
TWITTER_SCRAPER_ACTOR_ID = "u6ppkMWAx2E2MpEuF"  # For fetching tweets
TWITTER_REPLIES_SCRAPER_ACTOR_ID = "qhybbvlFivx7AP0Oh"  # For fetching replies

# Script generation settings (default mode)
DEFAULT_GENERATE_SCRIPT = True  # Generate scripts by default
DEFAULT_SCRIPT_STYLE = "engaging"  # Default to engaging style
DEFAULT_SCRIPT_MODEL = "deepseek/deepseek-r1-0528:free"  # Default to free model
