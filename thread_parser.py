"""
Thread parser module for the x-thread-dl tool.
Identifies threads from tweet replies and extracts relevant data.
"""

import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.thread_parser')

def identify_thread_videos(tweet_data: Dict[str, Any], replies_data: List[Dict[str, Any]], scraper) -> List[Dict[str, Any]]:
    """
    Identify a thread from tweet replies and extract video URLs.
    
    A thread is defined as consecutive replies from the same author as the original tweet.
    
    Args:
        tweet_data (Dict[str, Any]): The original tweet data
        replies_data (List[Dict[str, Any]]): List of reply data
        scraper: The scraper instance with extract_video_url method
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing author_screen_name, tweet_id, and video_url
    """
    try:
        # Check if tweet_data is valid
        if not tweet_data:
            logger.error("No tweet data provided")
            return []
        
        # Extract original author information
        original_author = _extract_author_screen_name(tweet_data)
        if not original_author:
            logger.error("Could not extract original author information")
            return []
        
        logger.info(f"Original tweet author: {original_author}")
        
        # Initialize the result list with the original tweet if it has a video
        result = []
        
        # Extract video URL from the original tweet
        original_tweet_id = tweet_data.get('id_str') or tweet_data.get('id')
        original_video_url = scraper.extract_video_url(tweet_data)
        
        if original_video_url:
            result.append({
                'author_screen_name': original_author,
                'tweet_id': original_tweet_id,
                'video_url': original_video_url
            })
            logger.info(f"Found video in original tweet: {original_tweet_id}")
        
        # Process replies to identify thread and extract videos
        for reply in replies_data:
            reply_author = _extract_author_screen_name(reply)
            
            # If the reply is not from the original author, the thread is broken
            if reply_author != original_author:
                logger.info(f"Thread broken: Reply from {reply_author} (not the original author)")
                break
            
            # Extract video URL from the reply
            reply_id = reply.get('id_str') or reply.get('id')
            video_url = scraper.extract_video_url(reply)
            
            if video_url:
                result.append({
                    'author_screen_name': reply_author,
                    'tweet_id': reply_id,
                    'video_url': video_url
                })
                logger.info(f"Found video in thread reply: {reply_id}")
        
        logger.info(f"Identified {len(result)} videos in the thread")
        return result
        
    except Exception as e:
        logger.error(f"Error identifying thread videos: {str(e)}", exc_info=True)
        return []

def _extract_author_screen_name(tweet_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract the author's screen name from tweet data.
    
    Args:
        tweet_data (Dict[str, Any]): The tweet data
        
    Returns:
        Optional[str]: The author's screen name or None if extraction failed
    """
    try:
        # Try different possible locations for the author information
        if 'user' in tweet_data and 'screen_name' in tweet_data['user']:
            return tweet_data['user']['screen_name']
        
        if 'author' in tweet_data and 'screen_name' in tweet_data['author']:
            return tweet_data['author']['screen_name']
        
        if 'author' in tweet_data and isinstance(tweet_data['author'], str):
            return tweet_data['author']
        
        # For reply data from the Twitter Replies Scraper
        if 'username' in tweet_data:
            return tweet_data['username']
        
        return None
    except Exception as e:
        logger.error(f"Error extracting author screen name: {str(e)}", exc_info=True)
        return None
