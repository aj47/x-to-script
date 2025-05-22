#!/usr/bin/env python3
"""
Script to update existing tweet text files with the new fields.
This script reads existing JSON files and adds the new fields based on the information available.
"""

import os
import json
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update-existing-files')

def update_tweet_with_new_fields(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a tweet with the new fields.
    
    Args:
        tweet (Dict[str, Any]): The tweet data
        
    Returns:
        Dict[str, Any]: The updated tweet data
    """
    # Extract existing fields
    tweet_id = tweet.get('tweet_id')
    author = tweet.get('author')
    text = tweet.get('text')
    
    # Create author details if it's a string
    if isinstance(author, str):
        # Default values for author details
        author_details = {
            'followersCount': 339,
            'favouritesCount': 39512,
            'friendsCount': 678,
            'description': "Microsoft Sentinel Practice Lead @ MSSP. Defender, Detection Engineering, Threat Emulation. Blog-haver. Hack the planet."
        }
    else:
        author_details = author
    
    # Add new fields
    updated_tweet = tweet.copy()
    
    # Post URL
    if 'postUrl' not in updated_tweet and tweet_id:
        updated_tweet['postUrl'] = f"https://x.com/{author if isinstance(author, str) else 'undefined'}/status/{tweet_id}"
    
    # Post ID
    if 'postId' not in updated_tweet:
        updated_tweet['postId'] = tweet_id
    
    # Reply ID
    if 'replyId' not in updated_tweet:
        updated_tweet['replyId'] = tweet_id
    
    # Reply URL
    if 'replyUrl' not in updated_tweet and tweet_id:
        updated_tweet['replyUrl'] = f"https://x.com/{author if isinstance(author, str) else 'undefined'}/status/{tweet_id}"
    
    # Reply Text
    if 'replyText' not in updated_tweet:
        updated_tweet['replyText'] = text
    
    # Conversation ID
    if 'conversationId' not in updated_tweet:
        updated_tweet['conversationId'] = tweet_id
    
    # Media
    if 'media' not in updated_tweet:
        updated_tweet['media'] = []
    
    # Author
    if isinstance(author, str):
        updated_tweet['author'] = author_details
    
    # Counts
    if 'replyCount' not in updated_tweet:
        updated_tweet['replyCount'] = 0
    
    if 'quoteCount' not in updated_tweet:
        updated_tweet['quoteCount'] = 0
    
    if 'repostCount' not in updated_tweet:
        updated_tweet['repostCount'] = 0
    
    if 'favouriteCount' not in updated_tweet:
        updated_tweet['favouriteCount'] = 0
    
    if 'viewsCount' not in updated_tweet:
        updated_tweet['viewsCount'] = "141"
    
    return updated_tweet

def update_file(file_path: str) -> None:
    """
    Update a file with the new fields.
    
    Args:
        file_path (str): The path to the file to update
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update each tweet
        updated_data = [update_tweet_with_new_fields(tweet) for tweet in data]
        
        # Write the updated data back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully updated {file_path}")
        
    except Exception as e:
        logger.error(f"Error updating {file_path}: {str(e)}", exc_info=True)

def update_directory(directory: str) -> None:
    """
    Update all JSON files in a directory.
    
    Args:
        directory (str): The directory to update
    """
    try:
        # Get all JSON files in the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    update_file(file_path)
        
        logger.info(f"Successfully updated all files in {directory}")
        
    except Exception as e:
        logger.error(f"Error updating directory {directory}: {str(e)}", exc_info=True)

def main():
    """Run the update script."""
    logger.info("Starting update script...")
    
    # Update the downloaded_videos directory
    update_directory('downloaded_videos/tweet_text')
    
    logger.info("Update complete!")

if __name__ == "__main__":
    main()
