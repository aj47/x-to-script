"""
Text extractor module for the x-thread-dl tool.
Extracts and stores text data from X.com (Twitter) tweets.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.text_extractor')

def extract_tweet_text(tweet_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract text and metadata from a tweet.
    
    Args:
        tweet_data (Dict[str, Any]): The tweet data
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing extracted text and metadata
        including additional fields like postUrl, postId, replyId, replyUrl, conversationId,
        media, expanded author details, and various counts
    """
    try:
        # Check if tweet_data is valid
        if not tweet_data:
            logger.error("No tweet data provided")
            return None
        
        # Extract tweet ID - check multiple possible field names
        tweet_id = (
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
        
        if not tweet_id:
            # Log the keys to help diagnose the issue
            logger.error(f"Could not extract tweet ID. Available keys: {list(tweet_data.keys())}")
            return None
        
        # Extract author information - check multiple possible field structures
        author = None
        if 'user' in tweet_data and 'screen_name' in tweet_data['user']:
            author = tweet_data['user']['screen_name']
        elif 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'screen_name' in tweet_data['author']:
            author = tweet_data['author']['screen_name']
        elif 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'username' in tweet_data['author']:
            author = tweet_data['author']['username']  # Twitter Replies Scraper format
        elif 'author' in tweet_data and isinstance(tweet_data['author'], dict) and 'name' in tweet_data['author']:
            author = tweet_data['author']['name']  # Twitter Replies Scraper format
        # Try to extract username from replyUrl if available
        elif 'replyUrl' in tweet_data:
            try:
                # Extract username from URL like https://x.com/username/status/123456789
                url_parts = tweet_data['replyUrl'].split('/')
                if len(url_parts) >= 4 and url_parts[2] in ['x.com', 'twitter.com']:
                    potential_username = url_parts[3]
                    if potential_username != 'undefined' and potential_username != 'status':
                        author = potential_username
            except Exception as e:
                logger.debug(f"Error extracting username from replyUrl: {str(e)}")
        elif 'author' in tweet_data and isinstance(tweet_data['author'], str):
            author = tweet_data['author']
        elif 'username' in tweet_data:
            author = tweet_data['username']
        elif 'user_screen_name' in tweet_data:
            author = tweet_data['user_screen_name']
        elif 'screen_name' in tweet_data:
            author = tweet_data['screen_name']
        elif 'userName' in tweet_data:
            author = tweet_data['userName']
        
        if not author:
            logger.error(f"Could not extract author for tweet {tweet_id}. Available keys: {list(tweet_data.keys())}")
            # Don't return None here, continue with extraction even if author is missing
            author = "unknown"  # Use a placeholder instead of failing
        
        # Extract text content - check multiple possible field names
        text = None
        if 'full_text' in tweet_data:
            text = tweet_data['full_text']
        elif 'text' in tweet_data:
            text = tweet_data['text']
        elif 'content' in tweet_data:
            text = tweet_data['content']
        elif 'tweet_text' in tweet_data:
            text = tweet_data['tweet_text']
        elif 'replyText' in tweet_data:  # Twitter Replies Scraper format
            text = tweet_data['replyText']
        elif 'body' in tweet_data:
            text = tweet_data['body']
        elif 'message' in tweet_data:
            text = tweet_data['message']
        
        if not text:
            logger.warning(f"Could not extract text content for tweet {tweet_id}. Available keys: {list(tweet_data.keys())}")
            text = ""  # Use empty string if no text is found
        
        # Extract timestamp - check multiple possible field names
        timestamp = None
        if 'created_at' in tweet_data:
            timestamp = tweet_data['created_at']
        elif 'date' in tweet_data:
            timestamp = tweet_data['date']
        elif 'timestamp' in tweet_data:
            timestamp = tweet_data['timestamp']
        elif 'time' in tweet_data:
            timestamp = tweet_data['time']
        elif 'createdAt' in tweet_data:
            timestamp = tweet_data['createdAt']
        
        # Extract URLs
        urls = []
        if 'entities' in tweet_data and 'urls' in tweet_data['entities']:
            for url_entity in tweet_data['entities']['urls']:
                if 'expanded_url' in url_entity:
                    urls.append(url_entity['expanded_url'])
        
        # Extract hashtags
        hashtags = []
        if 'entities' in tweet_data and 'hashtags' in tweet_data['entities']:
            for hashtag_entity in tweet_data['entities']['hashtags']:
                if 'text' in hashtag_entity:
                    hashtags.append(f"#{hashtag_entity['text']}")
        
        # Extract mentions
        mentions = []
        if 'entities' in tweet_data and 'user_mentions' in tweet_data['entities']:
            for mention_entity in tweet_data['entities']['user_mentions']:
                if 'screen_name' in mention_entity:
                    mentions.append(f"@{mention_entity['screen_name']}")
        
        # Extract reply information - check multiple possible field names
        is_reply = (
            tweet_data.get('in_reply_to_status_id') is not None or
            tweet_data.get('in_reply_to_status_id_str') is not None or
            tweet_data.get('isReply') is True or
            tweet_data.get('is_reply') is True or
            tweet_data.get('replyTo') is not None or
            tweet_data.get('reply_to') is not None
        )
        
        reply_to = (
            tweet_data.get('in_reply_to_screen_name') or
            tweet_data.get('replyToUser') or
            tweet_data.get('reply_to_user') or
            tweet_data.get('replyToScreenName') or
            tweet_data.get('reply_to_screen_name')
        )
        
        reply_to_id = (
            tweet_data.get('in_reply_to_status_id') or
            tweet_data.get('in_reply_to_status_id_str') or
            tweet_data.get('replyToId') or
            tweet_data.get('reply_to_id') or
            tweet_data.get('replyToTweetId') or
            tweet_data.get('reply_to_tweet_id')
        )
        
        # Extract additional fields
        # Post URL
        post_url = None
        if 'postUrl' in tweet_data:
            post_url = tweet_data['postUrl']
        elif tweet_id:
            post_url = f"https://x.com/{author}/status/{tweet_id}"
        
        # Post ID (same as tweet_id in most cases)
        post_id = tweet_data.get('postId') or tweet_id
        
        # Reply ID
        reply_id = tweet_data.get('replyId') or tweet_id
        
        # Reply URL
        reply_url = None
        if 'replyUrl' in tweet_data:
            reply_url = tweet_data['replyUrl']
        elif reply_id:
            reply_url = f"https://x.com/{author}/status/{reply_id}"
        
        # Conversation ID
        conversation_id = tweet_data.get('conversationId') or tweet_data.get('conversation_id') or tweet_id
        
        # Media
        media = []
        if 'media' in tweet_data:
            media = tweet_data['media']
        elif 'entities' in tweet_data and 'media' in tweet_data['entities']:
            for media_entity in tweet_data['entities']['media']:
                if 'media_url_https' in media_entity:
                    media.append(media_entity['media_url_https'])
        
        # Extract author details
        author_details = {}
        if 'author' in tweet_data and isinstance(tweet_data['author'], dict):
            author_details = tweet_data['author']
        elif 'user' in tweet_data:
            # Extract relevant user fields
            user_data = tweet_data['user']
            author_details = {
                'followersCount': user_data.get('followers_count'),
                'favouritesCount': user_data.get('favourites_count'),
                'friendsCount': user_data.get('friends_count'),
                'description': user_data.get('description')
            }
        
        # Extract counts
        reply_count = tweet_data.get('replyCount') or tweet_data.get('reply_count') or 0
        quote_count = tweet_data.get('quoteCount') or tweet_data.get('quote_count') or 0
        repost_count = tweet_data.get('repostCount') or tweet_data.get('repost_count') or tweet_data.get('retweet_count') or 0
        favourite_count = tweet_data.get('favouriteCount') or tweet_data.get('favorite_count') or tweet_data.get('favorite_count') or 0
        views_count = tweet_data.get('viewsCount') or tweet_data.get('views_count') or "0"
        
        # Construct result
        result = {
            'tweet_id': tweet_id,
            'author': author,
            'text': text,
            'timestamp': timestamp,
            'urls': urls,
            'hashtags': hashtags,
            'mentions': mentions,
            'is_reply': is_reply,
            'reply_to': reply_to,
            'reply_to_id': reply_to_id,
            'postUrl': post_url,
            'postId': post_id,
            'replyId': reply_id,
            'replyUrl': reply_url,
            'replyText': text,  # Same as text
            'conversationId': conversation_id,
            'media': media,
            'author': {
                **author_details
            } if author_details else author,  # Use author_details if available, otherwise use author string
            'replyCount': reply_count,
            'quoteCount': quote_count,
            'repostCount': repost_count,
            'favouriteCount': favourite_count,
            'viewsCount': views_count
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting text from tweet: {str(e)}", exc_info=True)
        return None

def extract_thread_text(tweet_data: Dict[str, Any], replies_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract text from a thread (original tweet and its replies).
    
    Args:
        tweet_data (Dict[str, Any]): The original tweet data
        replies_data (List[Dict[str, Any]]): List of reply data
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing extracted text and metadata
    """
    try:
        # Check if tweet_data is valid
        if not tweet_data:
            logger.error("No tweet data provided")
            return []
        
        # Initialize the result list with the original tweet
        result = []
        
        # Extract text from the original tweet
        original_tweet_text = extract_tweet_text(tweet_data)
        if original_tweet_text:
            result.append(original_tweet_text)
            logger.info(f"Extracted text from original tweet: {original_tweet_text['tweet_id']}")
        
        # Extract text from replies
        for reply in replies_data:
            reply_text = extract_tweet_text(reply)
            if reply_text:
                result.append(reply_text)
                logger.info(f"Extracted text from reply: {reply_text['tweet_id']}")
        
        logger.info(f"Extracted text from {len(result)} tweets in the thread")
        return result
        
    except Exception as e:
        logger.error(f"Error extracting thread text: {str(e)}", exc_info=True)
        return []

def save_thread_text(thread_text: List[Dict[str, Any]], output_dir: str, original_author: str, original_tweet_id: str) -> Optional[str]:
    """
    Save thread text to a JSON file.
    
    Args:
        thread_text (List[Dict[str, Any]]): List of dictionaries containing extracted text and metadata
        output_dir (str): The directory to save the text data to
        original_author (str): The screen name of the original tweet author
        original_tweet_id (str): The ID of the original tweet
        
    Returns:
        Optional[str]: The path to the saved file or None if saving failed
    """
    try:
        # Ensure output directory exists
        text_output_dir = os.path.join(output_dir, "tweet_text")
        os.makedirs(text_output_dir, exist_ok=True)
        
        # Construct the output filename
        output_filename = f"{original_author}_{original_tweet_id}_thread.json"
        output_path = os.path.join(text_output_dir, output_filename)
        
        logger.info(f"Saving thread text to {output_path}")
        
        # Save the thread text to a JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(thread_text, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved thread text to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving thread text: {str(e)}", exc_info=True)
        return None
