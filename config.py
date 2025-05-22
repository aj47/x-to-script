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
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_videos")

# Apify actor IDs
TWITTER_SCRAPER_ACTOR_ID = "u6ppkMWAx2E2MpEuF"  # For fetching tweets
TWITTER_REPLIES_SCRAPER_ACTOR_ID = "qhybbvlFivx7AP0Oh"  # For fetching replies
