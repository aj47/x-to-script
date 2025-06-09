"""
Media downloader module for the x-thread-dl tool.
Handles downloading videos from X.com (Twitter) using yt-dlp
and saving text content.
"""

import os
import json
import logging
import yt_dlp
from typing import Optional, Dict, List, Any

# Import configuration
import config # To get DEFAULT_OUTPUT_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO, # Changed to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.media_downloader') # Renamed logger

def _ensure_dir_exists(dir_path: str):
    """Ensure directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.debug(f"Created directory: {dir_path}")

def _save_json_content(data: Dict[str, Any], file_path: str):
    """Saves dictionary data as JSON to the specified file path."""
    try:
        _ensure_dir_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved JSON content to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON content to {file_path}: {str(e)}", exc_info=True)

def download_video_content(video_url: str, video_id: str, output_dir: str) -> Optional[str]:
    """
    Download a single video using yt-dlp.
    The filename will be {video_id}.mp4.

    Args:
        video_url (str): The URL of the video to download.
        video_id (str): The ID of the tweet/reply containing the video (used for filename).
        output_dir (str): The directory to save the video to.
        
    Returns:
        Optional[str]: The path to the downloaded video or None if download failed.
    """
    try:
        _ensure_dir_exists(output_dir)
        
        output_filename = f"{video_id}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"Downloading video from {video_url} to {output_path}")
        
        ydl_opts = {
            # Prioritize highest quality MP4, then highest quality overall
            'format': 'best[ext=mp4][height>=2160]/best[ext=mp4][height>=1080]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'quiet': False, # Set to False to see yt-dlp output, True for silent
            'no_warnings': False,
            'ignoreerrors': True,
            'nooverwrites': False, # Allow overwriting for retries or updates
            'retries': 5,
            'logger': logger, # Pass our logger to yt-dlp
            # Consider adding user agent if facing blocks:
            # 'http_headers': {'User-Agent': 'Mozilla/5.0 ...'}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get info about the video before downloading to log quality
            try:
                info = ydl.extract_info(video_url, download=False)
                if info:
                    format_info = info.get('format', 'unknown format')
                    resolution = f"{info.get('width', '?')}x{info.get('height', '?')}"
                    filesize = info.get('filesize') or info.get('filesize_approx')
                    size_mb = f"{filesize / (1024*1024):.1f}MB" if filesize else "unknown size"
                    logger.info(f"Downloading video: {resolution} ({format_info}) - {size_mb}")
            except Exception as e:
                logger.warning(f"Could not extract video info for logging: {e}")

            ydl.download([video_url])
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully downloaded video to {output_path}")
            return output_path
        else:
            # yt-dlp with ignoreerrors might not raise an exception but still fail
            logger.warning(f"Video file not found or empty after download attempt: {output_path}")
            # Check if a .part file exists, indicating an interrupted download
            part_file = output_path + ".part"
            if os.path.exists(part_file):
                logger.warning(f"Partial download file found: {part_file}. Download may have been interrupted.")
            return None
            
    except Exception as e:
        # This catches errors during yt-dlp instantiation or other unexpected issues
        logger.error(f"Error downloading video {video_id} from {video_url}: {str(e)}", exc_info=True)
        return None

def save_parsed_thread_data(parsed_data: Dict[str, Any], base_output_dir: str = config.DEFAULT_OUTPUT_DIR) -> List[str]:
    """
    Saves all parsed thread data (text and videos) according to the structured format:
    output/{user_screen_name}/{thread_id}/thread_text.json
    output/{user_screen_name}/{thread_id}/videos/{tweet_id}.mp4
    output/{user_screen_name}/{thread_id}/replies/{reply_id}/reply_text.json
    output/{user_screen_name}/{thread_id}/replies/{reply_id}/videos/{reply_id}.mp4

    Args:
        parsed_data (Dict[str, Any]): The structured data from thread_parser.
        base_output_dir (str): The base directory for all output (e.g., "output").
        
    Returns:
        List[str]: List of paths to all successfully saved/downloaded files.
    """
    if not parsed_data:
        logger.warning("No parsed data provided to save.")
        return []

    user_screen_name = parsed_data.get("user_screen_name", "unknown_user")
    thread_id = parsed_data.get("thread_id", "unknown_thread")

    # Path for the current thread: output/{user_screen_name}/{thread_id}/
    thread_path = os.path.join(base_output_dir, user_screen_name, thread_id)
    _ensure_dir_exists(thread_path)

    saved_files = []

    # 1. Save main thread text content
    thread_text_content = parsed_data.get("thread_text_content")
    if thread_text_content:
        thread_text_path = os.path.join(thread_path, "thread_text.json")
        _save_json_content(thread_text_content, thread_text_path)
        saved_files.append(thread_text_path)

    # 2. Download main thread videos
    thread_videos_path = os.path.join(thread_path, "videos")
    for video_info in parsed_data.get("thread_videos", []):
        video_url = video_info.get("video_url")
        # Use main thread_id for its videos, as video_info.tweet_id is the same
        video_id_for_filename = thread_id 
        if video_url and video_id_for_filename:
            downloaded_path = download_video_content(video_url, video_id_for_filename, thread_videos_path)
            if downloaded_path:
                saved_files.append(downloaded_path)
    
    # 3. Process replies
    replies_base_path = os.path.join(thread_path, "replies")
    for reply_info in parsed_data.get("replies", []):
        reply_id = reply_info.get("reply_id")
        if not reply_id:
            logger.warning(f"Skipping reply due to missing ID: {str(reply_info)[:100]}")
            continue

        # Path for the current reply: .../{thread_id}/replies/{reply_id}/
        current_reply_path = os.path.join(replies_base_path, reply_id)
        _ensure_dir_exists(current_reply_path)

        # 3a. Save reply text content
        reply_text_content = reply_info.get("reply_text_content")
        if reply_text_content:
            reply_text_path = os.path.join(current_reply_path, "reply_text.json")
            _save_json_content(reply_text_content, reply_text_path)
            saved_files.append(reply_text_path)
        
        # 3b. Download reply videos
        reply_videos_path = os.path.join(current_reply_path, "videos")
        for video_info in reply_info.get("reply_videos", []):
            video_url = video_info.get("video_url")
            # video_info.tweet_id here is actually the reply_id
            video_id_for_filename = video_info.get("tweet_id", reply_id) 
            if video_url and video_id_for_filename:
                downloaded_path = download_video_content(video_url, video_id_for_filename, reply_videos_path)
                if downloaded_path:
                    saved_files.append(downloaded_path)
                    
    logger.info(f"Finished processing and saving data for thread {user_screen_name}/{thread_id}. Total files saved/downloaded: {len(saved_files)}")
    return saved_files
