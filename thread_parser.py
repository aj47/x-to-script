"""
Thread parser module for the x-thread-dl tool.
Extracts relevant data from tweets and their replies for structured output.
"""

import logging
from typing import Dict, List, Any, Optional

# Import Scraper type for type hinting
from scraper import Scraper

# Set up logging
logging.basicConfig(
    level=logging.INFO, # Changed to INFO for less verbose default logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.thread_parser')

def _extract_tweet_id(tweet_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract the tweet ID from tweet data, checking multiple common fields.
    """
    if not tweet_data:
        return None
    return (
        tweet_data.get('id_str') or
        tweet_data.get('rest_id') or # Often used in newer API responses
        tweet_data.get('id') or
        tweet_data.get('tweetId') or
        tweet_data.get('tweet_id') or
        tweet_data.get('postId') or
        tweet_data.get('post_id') or
        tweet_data.get('statusId') or
        tweet_data.get('status_id') or
        tweet_data.get('replyId') # As seen in some reply structures
    )

def _extract_author_screen_name(tweet_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract the author's screen name from tweet data.
    Tries various common fields where screen name/username might be located.
    """
    if not tweet_data:
        return None
    try:
        # Standard tweet object structure
        if 'user' in tweet_data and isinstance(tweet_data['user'], dict) and 'screen_name' in tweet_data['user']:
            return tweet_data['user']['screen_name']
        
        # Apify actor specific structures (often under 'author')
        if 'author' in tweet_data and isinstance(tweet_data['author'], dict):
            author_info = tweet_data['author']
            return (
                author_info.get('screen_name') or
                author_info.get('username') or # Common in replies actor
                author_info.get('name') # Fallback if screen_name/username not present
            )

        # Direct fields (sometimes present in simplified objects or replies)
        direct_fields = ['username', 'user_screen_name', 'screen_name', 'userName']
        for field in direct_fields:
            if field in tweet_data and isinstance(tweet_data[field], str):
                return tweet_data[field]

        # Fallback: Try to get from 'user_mentions' if it's a self-reply or similar context
        if 'user_mentions' in tweet_data and isinstance(tweet_data['user_mentions'], list):
            for mention in tweet_data['user_mentions']:
                if isinstance(mention, dict) and 'screen_name' in mention:
                    # This is a heuristic, might need refinement based on typical data
                    # For now, let's assume if user_mentions is the only source, it might be the author
                    # This part is speculative and should be tested.
                    pass # logger.debug("Considering screen_name from user_mentions as a fallback.")

        # Try to extract username from replyUrl if available (often in replies data)
        if 'replyUrl' in tweet_data and isinstance(tweet_data['replyUrl'], str):
            url_parts = tweet_data['replyUrl'].split('/')
            if len(url_parts) >= 4 and url_parts[2] in ['x.com', 'twitter.com']:
                potential_username = url_parts[3]
                if potential_username not in ['undefined', 'status', 'i', 'web']: # 'i' and 'web' are common non-username paths
                    return potential_username
        
        # If 'author' is just a string (less common, but possible)
        if 'author' in tweet_data and isinstance(tweet_data['author'], str):
            return tweet_data['author']

        logger.debug(f"Could not extract author screen name. Available keys: {list(tweet_data.keys())}")
        if 'author' in tweet_data:
            logger.debug(f"Author field details: Type={type(tweet_data['author'])}, Value={str(tweet_data['author'])[:100]}")
        if 'user' in tweet_data:
            logger.debug(f"User field details: Type={type(tweet_data['user'])}, Value={str(tweet_data['user'])[:100]}")
            
        return None
    except Exception as e:
        logger.error(f"Error extracting author screen name: {str(e)}", exc_info=True)
        return None

def parse_tweet_and_replies_data(
    tweet_data: Dict[str, Any], 
    replies_data: List[Dict[str, Any]], 
    scraper: Scraper
) -> Optional[Dict[str, Any]]:
    """
    Parses the main tweet and all its replies to extract structured data
    for saving text and videos according to the user/thread/reply hierarchy.

    Args:
        tweet_data (Dict[str, Any]): The original tweet data from the scraper.
        replies_data (List[Dict[str, Any]]): List of reply data from the scraper.
        scraper (Scraper): The scraper instance, used for its extract_video_url method.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing structured data for the thread
                                  and its replies, or None if essential data is missing.
    """
    if not tweet_data:
        logger.error("Main tweet data is missing. Cannot parse.")
        return None

    main_author_screen_name = _extract_author_screen_name(tweet_data)
    main_tweet_id = _extract_tweet_id(tweet_data)

    if not main_author_screen_name:
        logger.error(f"Could not extract author screen name from main tweet. Data: {str(tweet_data)[:500]}")
        # Attempt to get a fallback user identifier if screen_name is missing
        main_author_screen_name = tweet_data.get('user', {}).get('id_str') or "unknown_user"
        logger.warning(f"Using fallback user identifier: {main_author_screen_name}")

    if not main_tweet_id:
        logger.error(f"Could not extract ID from main tweet. Data: {str(tweet_data)[:500]}")
        return None # Thread ID is crucial

    logger.info(f"Parsing thread by '{main_author_screen_name}', main tweet ID: '{main_tweet_id}'")

    parsed_data = {
        "user_screen_name": main_author_screen_name,
        "thread_id": main_tweet_id,
        "thread_text_content": tweet_data, # Store the full original tweet data
        "thread_videos": [],
        "replies": []
    }

    # Process main tweet for videos
    main_video_url = scraper.extract_video_url(tweet_data)
    if main_video_url:
        parsed_data["thread_videos"].append({
            "tweet_id": main_tweet_id, # Redundant here but good for consistency if a tweet could have multiple distinct video entries
            "video_url": main_video_url
        })
        logger.info(f"Found video in main tweet {main_tweet_id}: {main_video_url}")

    # Process all replies
    if replies_data is None: # Handle case where replies_data might be None from scraper
        replies_data = []
        logger.warning("Replies data is None, processing as an empty list of replies.")

    for i, reply_content in enumerate(replies_data):
        if not reply_content:
            logger.warning(f"Skipping empty reply data at index {i}.")
            continue

        reply_id = _extract_tweet_id(reply_content)
        reply_author_screen_name = _extract_author_screen_name(reply_content)

        if not reply_id:
            logger.warning(f"Could not extract ID for reply at index {i}. Skipping. Data: {str(reply_content)[:200]}")
            continue
        
        if not reply_author_screen_name:
            logger.warning(f"Could not extract author for reply {reply_id}. Using 'unknown_reply_author'. Data: {str(reply_content)[:200]}")
            reply_author_screen_name = "unknown_reply_author"
        
        logger.debug(f"Processing reply {reply_id} by {reply_author_screen_name}")

        reply_struct = {
            "reply_id": reply_id,
            "reply_author_screen_name": reply_author_screen_name,
            "reply_text_content": reply_content, # Store the full reply data
            "reply_videos": []
        }

        reply_video_url = scraper.extract_video_url(reply_content)
        if reply_video_url:
            reply_struct["reply_videos"].append({
                "tweet_id": reply_id, # ID of the reply tweet itself
                "video_url": reply_video_url
            })
            logger.info(f"Found video in reply {reply_id}: {reply_video_url}")
        
        parsed_data["replies"].append(reply_struct)

    logger.info(f"Finished parsing. Found {len(parsed_data['thread_videos'])} video(s) in main thread, and {len(parsed_data['replies'])} replies processed.")
    total_reply_videos = sum(len(r['reply_videos']) for r in parsed_data['replies'])
    logger.info(f"Total videos found in replies: {total_reply_videos}")
    
    return parsed_data
