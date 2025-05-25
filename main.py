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

# Import local modules
import config
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
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose (DEBUG level) output')
@click.option('--list-formats', is_flag=True, help='List available video formats before downloading')
@click.option('--skip-script', is_flag=True, help='Skip automatic TikTok script generation')
@click.option('--openrouter-key', '-k', default=None,
              help='OpenRouter API key for script generation (can also be set as OPENROUTER_API_KEY environment variable)')
@click.option('--model', '-m', default=None,
              help='OpenRouter model to use for script generation (default: claude-3.5-sonnet)')
def main(tweet_url: str, reply_limit: int, output_dir: str, apify_token: Optional[str], verbose: bool, list_formats: bool,
         skip_script: bool, openrouter_key: Optional[str], model: Optional[str]):
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

    asyncio.run(process_thread_and_replies(tweet_url, reply_limit, output_dir, effective_api_token, list_formats,
                                         skip_script, openrouter_key, model))

async def process_thread_and_replies(tweet_url: str, reply_limit: int, base_output_dir: str, api_token: str,
                                   list_formats: bool = False, skip_script: bool = False,
                                   openrouter_key: Optional[str] = None, model: Optional[str] = None):
    """
    Process a tweet URL to fetch, parse, and save the thread and its replies.
    Automatically generates TikTok scripts unless skip_script is True.
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
        saved_media_files = save_parsed_thread_data(parsed_data, base_output_dir, list_formats)

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

            # Automatically generate TikTok script unless skipped
            if not skip_script:
                await generate_tiktok_script_automatically(final_output_location, openrouter_key, model)

    except Exception as e:
        logger.error(f"An critical error occurred during processing: {str(e)}", exc_info=True)
        sys.exit(1)

async def generate_tiktok_script_automatically(thread_dir: str, openrouter_key: Optional[str] = None,
                                             model: Optional[str] = None):
    """
    Automatically generate TikTok script from thread data.

    Args:
        thread_dir: Directory containing the thread data
        openrouter_key: OpenRouter API key
        model: Model to use for generation
    """
    try:
        # Look for thread_text.json file
        thread_json_path = os.path.join(thread_dir, "thread_text.json")

        if not os.path.exists(thread_json_path):
            logger.warning(f"No thread_text.json found in {thread_dir}, skipping script generation")
            return

        logger.info("🎬 Generating TikTok script from thread data...")

        # Initialize script generator
        try:
            generator = ScriptGenerator(api_key=openrouter_key, model=model)
        except ValueError as e:
            logger.warning(f"⚠️ Script generation skipped: {str(e)}")
            logger.info("💡 To enable script generation, set OPENROUTER_API_KEY environment variable")
            return

        # Generate script in the same directory as the thread
        script_output_dir = os.path.join(thread_dir, "scripts")
        result = await generator.process_thread_file(thread_json_path, script_output_dir)

        if result:
            logger.info(f"✅ TikTok script generated: {result}")
        else:
            logger.warning("⚠️ Failed to generate TikTok script")

    except Exception as e:
        logger.warning(f"⚠️ Script generation failed: {str(e)}")
        logger.debug("Script generation error details:", exc_info=True)

@click.command()
@click.argument('json_file_path', required=True, type=click.Path(exists=True))
@click.option('--output-dir', '-o', default=None,
              type=click.Path(),
              help='Directory to save generated scripts (default: generated_scripts)')
@click.option('--model', '-m', default=None,
              help='OpenRouter model to use for generation (default: claude-3.5-sonnet)')
@click.option('--openrouter-key', '-k', default=None,
              help='OpenRouter API key (can also be set as OPENROUTER_API_KEY environment variable)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose (DEBUG level) output')
def generate_script(json_file_path: str, output_dir: Optional[str], model: Optional[str],
                   openrouter_key: Optional[str], verbose: bool):
    """
    Generate a TikTok video script from scraped Twitter thread data.

    JSON_FILE_PATH: Path to the JSON file containing scraped thread data.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled for script generation.")

    try:
        # Initialize script generator
        generator = ScriptGenerator(api_key=openrouter_key, model=model)

        # Process the thread file
        result = asyncio.run(generator.process_thread_file(json_file_path, output_dir))

        if result:
            logger.info(f"Successfully generated TikTok script: {result}")
            click.echo(f"✅ Script generated successfully: {result}")
        else:
            logger.error("Failed to generate script")
            click.echo("❌ Failed to generate script. Check logs for details.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during script generation: {str(e)}", exc_info=True)
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
