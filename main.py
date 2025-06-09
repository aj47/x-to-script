#!/usr/bin/env python3
"""
x-thread-dl: A CLI tool to download media (videos and text) from X.com (Twitter) threads and their replies.

Given a tweet URL, this tool:
1. Fetches the original tweet and its replies.
2. Parses the data to extract user information, thread ID, reply IDs, text content, and video URLs.
3. Saves the text content as JSON files and downloads videos into a structured directory:
   output/{user_screen_name}/{thread_id}/thread_text.json
   output/{user_screen_name}/{thread_id}/videos/{thread_id}.mp4
   output/{user_screen_name}/{thread_id}/replies/{reply_id}/reply_text.json
   output/{user_screen_name}/{thread_id}/replies/{reply_id}/videos/{reply_id}.mp4
"""

import os
import sys
import asyncio
import logging
import click
from typing import Optional
from pathlib import Path

# Import local modules
import config
import config_openrouter
from scraper import Scraper
from thread_parser import parse_tweet_and_replies_data # Updated import
from video_downloader import save_parsed_thread_data  # Updated import, was video_downloader
from script_generator import ScriptGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO, # Default to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl')

# Suppress verbose logging from external libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)

@click.command()
@click.argument('tweet_url', required=True)
@click.option('--reply-limit', '-r', default=config.DEFAULT_REPLY_LIMIT,
              type=int,
              help=f'Maximum number of replies to fetch (default: {config.DEFAULT_REPLY_LIMIT})')
@click.option('--output-dir', '-o', default=config.DEFAULT_OUTPUT_DIR,
              type=click.Path(),
              help=f'Base directory to save downloaded content (default: {config.DEFAULT_OUTPUT_DIR})')
@click.option('--apify-token', '-t', default=None,
              help='Apify API token (can also be set as APIFY_API_TOKEN environment variable or in a .env file)')
@click.option('--generate-script', '-g', is_flag=True,
              help='Generate TikTok script after downloading thread')
@click.option('--openrouter-key', '-k', default=None,
              help='OpenRouter API key for script generation (can also be set as OPENROUTER_API_KEY environment variable)')
@click.option('--script-style', '-s', default=config_openrouter.DEFAULT_SCRIPT_STYLE,
              type=click.Choice(list(config_openrouter.SCRIPT_STYLES.keys())),
              help=f'Script style for generation (default: {config_openrouter.DEFAULT_SCRIPT_STYLE})')
@click.option('--script-duration', '-d', default=config_openrouter.DEFAULT_TARGET_DURATION,
              type=int,
              help=f'Target script duration in seconds (default: {config_openrouter.DEFAULT_TARGET_DURATION})')
@click.option('--script-model', '-m', default=config.DEFAULT_SCRIPT_MODEL,
              type=click.Choice(config_openrouter.AVAILABLE_MODELS),
              help=f'LLM model for script generation (default: {config.DEFAULT_SCRIPT_MODEL})')
@click.option('--no-replies-in-script', is_flag=True,
              help='Exclude replies from script generation (only use main thread)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose (DEBUG level) output')
def main(tweet_url: str, reply_limit: int, output_dir: str, apify_token: Optional[str],
         generate_script: bool, openrouter_key: Optional[str], script_style: str,
         script_duration: int, script_model: str, no_replies_in_script: bool, verbose: bool):
    """
    Download media (videos and text) from X.com (Twitter) threads and replies.
    
    TWEET_URL: The URL of the initial tweet in the thread.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG) # Set root logger to DEBUG
        for handler in logging.getLogger().handlers: # Ensure all handlers also respect DEBUG
            handler.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled. All loggers set to DEBUG.")
    else:
        # Ensure other loggers (like apify_client) are not overly verbose if not in verbose mode
        logging.getLogger("apify_client").setLevel(logging.WARNING)
        logging.getLogger("yt_dlp").setLevel(logging.WARNING)


    if not ('twitter.com' in tweet_url or 'x.com' in tweet_url):
        logger.error(f"Invalid tweet URL: {tweet_url}. Must contain 'twitter.com' or 'x.com'.")
        sys.exit(1)
    
    effective_api_token = apify_token or config.APIFY_API_TOKEN
    if not effective_api_token:
        logger.error("No Apify API token provided. Set it with --apify-token, in a .env file, or as APIFY_API_TOKEN environment variable.")
        sys.exit(1)
    
    # The base output directory is passed; specific subdirs are created by save_parsed_thread_data
    # os.makedirs(output_dir, exist_ok=True) # This will be handled by save_parsed_thread_data's helpers

    asyncio.run(process_thread_and_replies(
        tweet_url, reply_limit, output_dir, effective_api_token,
        generate_script, openrouter_key, script_style, script_duration,
        script_model, no_replies_in_script
    ))

async def process_thread_and_replies(
    tweet_url: str, reply_limit: int, base_output_dir: str, api_token: str,
    generate_script: bool = False, openrouter_key: Optional[str] = None,
    script_style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
    script_duration: int = config_openrouter.DEFAULT_TARGET_DURATION,
    script_model: str = config.DEFAULT_SCRIPT_MODEL,
    no_replies_in_script: bool = False
):
    """
    Process a tweet URL to fetch, parse, and save the thread and its replies.
    """
    try:
        logger.info(f"Processing URL: {tweet_url}")
        
        scraper_instance = Scraper(api_token=api_token)
        
        logger.info(f"Fetching main tweet and up to {reply_limit} replies...")
        scraped_content = await scraper_instance.fetch_tweet_and_replies(tweet_url, reply_limit)
        
        main_tweet_data = scraped_content.get('tweet')
        replies_list_data = scraped_content.get('replies', []) # Default to empty list if None
        
        if not main_tweet_data:
            logger.error("Failed to fetch main tweet data. Aborting.")
            sys.exit(1)
        
        logger.info(f"Successfully fetched main tweet and {len(replies_list_data)} replies.")
        
        logger.info("Parsing fetched data...")
        # Pass the scraper instance for its utility functions like extract_video_url
        parsed_data = parse_tweet_and_replies_data(main_tweet_data, replies_list_data, scraper_instance)
        
        if not parsed_data:
            logger.error("Failed to parse tweet and reply data. Aborting.")
            sys.exit(1)
        
        user_name = parsed_data.get("user_screen_name", "unknown_user")
        tid = parsed_data.get("thread_id", "unknown_thread")
        logger.info(f"Data parsed for user '{user_name}', thread '{tid}'.")

        logger.info(f"Saving content to base directory: {base_output_dir}")
        saved_media_files = save_parsed_thread_data(parsed_data, base_output_dir)
        
        if not saved_media_files:
            logger.warning("No files were saved. This might be due to no content found or errors during saving/downloading.")
            # Decide if this is an error state or acceptable (e.g., thread with no videos/text worth saving)
            # For now, let's consider it a non-fatal warning if parsing was okay.
        else:
            logger.info(f"Successfully saved {len(saved_media_files)} file(s):")
            for file_path in saved_media_files:
                logger.info(f"  - {file_path}")
            
            final_output_location = os.path.join(base_output_dir, user_name, tid)
            logger.info(f"All content for this thread saved under: {os.path.abspath(final_output_location)}")

            # Generate TikTok script if requested
            if generate_script:
                await generate_tiktok_script(
                    Path(final_output_location), openrouter_key, script_style,
                    script_duration, script_model, no_replies_in_script
                )

    except Exception as e:
        logger.error(f"An critical error occurred during processing: {str(e)}", exc_info=True)
        sys.exit(1)

async def generate_tiktok_script(
    thread_dir: Path, openrouter_key: Optional[str], script_style: str,
    script_duration: int, script_model: str, no_replies_in_script: bool
):
    """
    Generate a TikTok script for the downloaded thread.

    Args:
        thread_dir (Path): Path to the thread directory
        openrouter_key (Optional[str]): OpenRouter API key
        script_style (str): Script style
        script_duration (int): Target duration in seconds
        script_model (str): LLM model to use
        no_replies_in_script (bool): Whether to exclude replies
    """
    try:
        logger.info("🎬 Generating TikTok script...")

        # Check if OpenRouter API key is available
        effective_openrouter_key = openrouter_key or config_openrouter.OPENROUTER_API_KEY
        if not effective_openrouter_key:
            logger.error(config_openrouter.ERROR_NO_API_KEY)
            return

        # Initialize script generator
        script_generator = ScriptGenerator(effective_openrouter_key, script_model)

        # Generate script
        script_data = await script_generator.process_thread_directory(
            thread_dir,
            style=script_style,
            target_duration=script_duration,
            include_replies=not no_replies_in_script
        )

        if script_data:
            # Save script
            script_file = thread_dir / "tiktok_script.json"
            if script_generator.save_script(script_data, script_file):
                logger.info(f"✅ TikTok script generated and saved to: {script_file}")

                # Log script summary
                if "hook" in script_data and "intro" in script_data and "explainer" in script_data:
                    logger.info("📝 Script Summary:")
                    logger.info(f"   Hook: {script_data['hook'].get('text', 'N/A')[:50]}...")
                    logger.info(f"   Style: {script_style}")
                    logger.info(f"   Duration: {script_duration}s")
                else:
                    logger.info("📝 Script generated (see file for details)")
            else:
                logger.error("❌ Failed to save TikTok script")
        else:
            logger.error("❌ Failed to generate TikTok script")

    except Exception as e:
        logger.error(f"Error generating TikTok script: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()
