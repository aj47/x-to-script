#!/usr/bin/env python3
"""
x-thread-dl: A CLI tool to download videos from X.com (Twitter) threads.

Given a tweet URL, this tool:
1. Downloads the original tweet and up to 50 replies
2. Identifies if the replies form a thread (consecutive replies from the original author)
3. Downloads videos from the thread
"""

import os
import sys
import asyncio
import logging
import click
from typing import Optional

# Import local modules
import config
from scraper import Scraper
import thread_parser
import video_downloader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl')

@click.command()
@click.argument('tweet_url', required=True)
@click.option('--reply-limit', '-r', default=config.DEFAULT_REPLY_LIMIT, 
              help=f'Maximum number of replies to fetch (default: {config.DEFAULT_REPLY_LIMIT})')
@click.option('--output-dir', '-o', default=config.DEFAULT_OUTPUT_DIR,
              help=f'Directory to save downloaded videos (default: {config.DEFAULT_OUTPUT_DIR})')
@click.option('--apify-token', '-t', default=None,
              help='Apify API token (can also be set as APIFY_API_TOKEN environment variable or in a .env file)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(tweet_url: str, reply_limit: int, output_dir: str, apify_token: Optional[str], verbose: bool):
    """
    Download videos from X.com (Twitter) threads.
    
    TWEET_URL: The URL of the tweet to download videos from.
    """
    # Set logging level based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    # Validate tweet URL
    if not ('twitter.com' in tweet_url or 'x.com' in tweet_url):
        logger.error(f"Invalid tweet URL: {tweet_url}")
        sys.exit(1)
    
    # Use the provided Apify token or the one from config
    api_token = apify_token or config.APIFY_API_TOKEN
    if not api_token:
        logger.error("No Apify API token provided. Set it with --apify-token, in a .env file, or as APIFY_API_TOKEN environment variable.")
        sys.exit(1)
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the main async function
    asyncio.run(process_tweet(tweet_url, reply_limit, output_dir, api_token))

async def process_tweet(tweet_url: str, reply_limit: int, output_dir: str, api_token: str):
    """
    Process a tweet URL to download thread videos.
    
    Args:
        tweet_url (str): The URL of the tweet to process
        reply_limit (int): Maximum number of replies to fetch
        output_dir (str): Directory to save downloaded videos
        api_token (str): Apify API token
    """
    try:
        logger.info(f"Processing tweet URL: {tweet_url}")
        
        # Initialize the scraper
        scraper = Scraper(api_token=api_token)
        
        # Fetch the tweet and its replies
        logger.info(f"Fetching tweet and up to {reply_limit} replies...")
        data = await scraper.fetch_tweet_and_replies(tweet_url, reply_limit)
        
        tweet = data.get('tweet')
        replies = data.get('replies', [])
        
        if not tweet:
            logger.error("Failed to fetch tweet data")
            sys.exit(1)
        
        logger.info(f"Successfully fetched tweet and {len(replies)} replies")
        
        # Identify thread videos
        logger.info("Identifying thread videos...")
        thread_videos = thread_parser.identify_thread_videos(tweet, replies, scraper)
        
        if not thread_videos:
            logger.warning("No videos found in the thread")
            sys.exit(0)
        
        logger.info(f"Found {len(thread_videos)} videos in the thread")
        
        # Download thread videos
        logger.info(f"Downloading {len(thread_videos)} videos to {output_dir}...")
        downloaded_videos = video_downloader.download_thread_videos(thread_videos, output_dir)
        
        if not downloaded_videos:
            logger.warning("Failed to download any videos")
            sys.exit(1)
        
        logger.info(f"Successfully downloaded {len(downloaded_videos)} videos:")
        for video_path in downloaded_videos:
            logger.info(f"  - {os.path.basename(video_path)}")
        
        logger.info(f"Videos saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        logger.error(f"Error processing tweet: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
