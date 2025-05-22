"""
Thread parser module for the x-thread-dl tool.
Identifies threads from tweet replies and extracts relevant data.
"""

import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.thread_parser')

def identify_thread_videos(tweet_data: Dict[str, Any], replies_data: List[Dict[str, Any]], scraper) -> List[Dict[str, Any]]:
    """
    Identify a thread from tweet replies and extract video URLs.
    
    A thread includes all replies from the same author as the original tweet,
    even if they are not consecutive (i.e., other users' replies are skipped).
    
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
        
        # Extract tweet ID from the original tweet - check multiple possible field names
        original_tweet_id = (
            tweet_data.get('id_str') or 
            tweet_data.get('id') or 
            tweet_data.get('tweetId') or 
            tweet_data.get('tweet_id') or 
            tweet_data.get('postId') or 
            tweet_data.get('post_id') or 
            tweet_data.get('statusId') or 
            tweet_data.get('status_id') or
            tweet_data.get('replyId')  # Added for Twitter Replies Scraper
        )
        original_video_url = scraper.extract_video_url(tweet_data)
        
        if original_video_url:
            result.append({
                'author_screen_name': original_author,
                'tweet_id': original_tweet_id,
                'video_url': original_video_url
            })
            logger.info(f"Found video in original tweet: {original_tweet_id}")
        
        # Process replies to identify thread and extract videos
        for i, reply in enumerate(replies_data):
            reply_author = _extract_author_screen_name(reply)
            reply_id = (
                reply.get('id_str') or 
                reply.get('id') or 
                reply.get('tweetId') or 
                reply.get('tweet_id') or 
                reply.get('postId') or 
                reply.get('post_id') or 
                reply.get('statusId') or 
                reply.get('status_id')
            )
            
            # Debug log the reply details
            logger.debug(f"Reply {i+1}: ID={reply_id}, Author={reply_author}, Original Author={original_author}")
            
            # If the reply is not from the original author, check if it mentions the original author
            if reply_author != original_author:
                # Check if the reply text mentions the original author
                reply_text = reply.get('replyText', '') or reply.get('text', '') or reply.get('full_text', '') or ''
                if f"@{original_author}" in reply_text:
                    logger.info(f"Reply from {reply_author} mentions the original author: {original_author}")
                else:
                    logger.info(f"Skipping reply from {reply_author} (not the original author)")
                    # Log the keys of the reply to help diagnose the issue
                    logger.debug(f"Reply {i+1} keys: {list(reply.keys())}")
                    continue
            
            # Extract tweet ID from the reply - check multiple possible field names
            reply_id = (
                reply.get('id_str') or 
                reply.get('id') or 
                reply.get('tweetId') or 
                reply.get('tweet_id') or 
                reply.get('postId') or 
                reply.get('post_id') or 
                reply.get('statusId') or 
                reply.get('status_id') or
                reply.get('replyId')  # Added for Twitter Replies Scraper
            )
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
        
        if 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'screen_name' in tweet_data['author']:
            return tweet_data['author']['screen_name']
        
        if 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'username' in tweet_data['author']:
            return tweet_data['author']['username']  # Twitter Replies Scraper format
        
        if 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'name' in tweet_data['author']:
            return tweet_data['author']['name']  # Twitter Replies Scraper format
        
        # Try to extract username from replyUrl if available
        if 'replyUrl' in tweet_data:
            try:
                # Extract username from URL like https://x.com/username/status/123456789
                url_parts = tweet_data['replyUrl'].split('/')
                if len(url_parts) >= 4 and url_parts[2] in ['x.com', 'twitter.com']:
                    potential_username = url_parts[3]
                    if potential_username != 'undefined' and potential_username != 'status':
                        return potential_username
            except Exception as e:
                logger.debug(f"Error extracting username from replyUrl: {str(e)}")
        
        if 'author' in tweet_data and isinstance(tweet_data['author'], str):
            return tweet_data['author']
        
        # For reply data from the Twitter Replies Scraper - check multiple possible field names
        if 'username' in tweet_data:
            return tweet_data['username']
        
        if 'user_screen_name' in tweet_data:
            return tweet_data['user_screen_name']
        
        if 'screen_name' in tweet_data:
            return tweet_data['screen_name']
        
        if 'userName' in tweet_data:
            return tweet_data['userName']
        
        # Log available keys if author can't be extracted
        logger.debug(f"Could not extract author screen name. Available keys: {list(tweet_data.keys())}")
        
        # If author field exists but we couldn't extract a username, log its structure
        if 'author' in tweet_data:
            logger.debug(f"Author field exists but couldn't extract username. Author type: {type(tweet_data['author'])}, Value: {tweet_data['author']}")
        
        return None
    except Exception as e:
        logger.error(f"Error extracting author screen name: {str(e)}", exc_info=True)
        return None
