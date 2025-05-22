"""
Video downloader module for the x-thread-dl tool.
Handles downloading videos from X.com (Twitter) using yt-dlp.
"""

import os
import logging
import yt_dlp
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.video_downloader')

def download_video(video_url: str, author_screen_name: str, tweet_id: str, output_dir: str) -> Optional[str]:
    """
    Download a video from X.com (Twitter) using yt-dlp.
    
    Args:
        video_url (str): The URL of the video to download
        author_screen_name (str): The screen name of the tweet author
        tweet_id (str): The ID of the tweet
        output_dir (str): The directory to save the video to
        
    Returns:
        Optional[str]: The path to the downloaded video or None if download failed
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct the output filename
        output_filename = f"{author_screen_name}_{tweet_id}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"Downloading video from {video_url} to {output_path}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer MP4 format
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,  # Continue on download errors
            'nooverwrites': False,  # Overwrite existing files
            'retries': 5,  # Retry a few times on connection errors
            'logger': logger,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Check if the file was downloaded successfully
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully downloaded video to {output_path}")
            return output_path
        else:
            logger.warning(f"Video file not found or empty: {output_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error downloading video from {video_url}: {str(e)}", exc_info=True)
        return None

def download_thread_videos(thread_videos: list, output_dir: str) -> list:
    """
    Download videos from a thread.
    
    Args:
        thread_videos (list): List of dictionaries containing author_screen_name, tweet_id, and video_url
        output_dir (str): The directory to save the videos to
        
    Returns:
        list: List of paths to the downloaded videos
    """
    downloaded_videos = []
    
    if not thread_videos:
        logger.warning("No videos to download")
        return downloaded_videos
    
    logger.info(f"Downloading {len(thread_videos)} videos from thread")
    
    for i, video_info in enumerate(thread_videos, 1):
        video_url = video_info.get('video_url')
        author_screen_name = video_info.get('author_screen_name')
        tweet_id = video_info.get('tweet_id')
        
        if not all([video_url, author_screen_name, tweet_id]):
            logger.warning(f"Missing required information for video {i}")
            continue
        
        logger.info(f"Downloading video {i}/{len(thread_videos)}: {author_screen_name}_{tweet_id}")
        
        video_path = download_video(video_url, author_screen_name, tweet_id, output_dir)
        
        if video_path:
            downloaded_videos.append(video_path)
    
    logger.info(f"Downloaded {len(downloaded_videos)}/{len(thread_videos)} videos")
    
    return downloaded_videos
