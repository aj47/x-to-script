#!/usr/bin/env python3
"""
Test script for the text extraction functionality.
This script simulates tweet data and tests the text extraction without making API calls.
"""

import os
import json
import logging
from text_extractor import extract_tweet_text, extract_thread_text, save_thread_text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test-text-extraction')

def create_mock_tweet():
    """Create a mock tweet for testing."""
    return {
        "id_str": "1925002086405832987",
        "user": {
            "screen_name": "cline",
            "followers_count": 339,
            "favourites_count": 39512,
            "friends_count": 678,
            "description": "Microsoft Sentinel Practice Lead @ MSSP. Defender, Detection Engineering, Threat Emulation. Blog-haver. Hack the planet."
        },
        "full_text": "This is a test tweet with #hashtag and @mention",
        "created_at": "Wed May 21 10:00:00 +0000 2025",
        "entities": {
            "urls": [
                {"expanded_url": "https://example.com"}
            ],
            "hashtags": [
                {"text": "hashtag"}
            ],
            "user_mentions": [
                {"screen_name": "mention"}
            ],
            "media": [
                {"media_url_https": "https://pbs.twimg.com/media/example.jpg"}
            ]
        },
        "in_reply_to_status_id": None,
        "in_reply_to_screen_name": None,
        "replyCount": 5,
        "quoteCount": 2,
        "repostCount": 10,
        "favouriteCount": 25,
        "viewsCount": "141",
        "conversationId": "1925002086405832987"
    }

def create_mock_reply():
    """Create a mock reply tweet for testing."""
    return {
        "id_str": "1925061330698174664",
        "user": {
            "screen_name": "cline",
            "followers_count": 339,
            "favourites_count": 39512,
            "friends_count": 678,
            "description": "Microsoft Sentinel Practice Lead @ MSSP. Defender, Detection Engineering, Threat Emulation. Blog-haver. Hack the planet."
        },
        "full_text": "@cline Everyday I'm shocked and perturbed by how good + how quickly these updates come out",
        "created_at": "Wed May 21 10:01:00 +0000 2025",
        "entities": {
            "urls": [],
            "hashtags": [],
            "user_mentions": [
                {"screen_name": "cline"}
            ]
        },
        "in_reply_to_status_id": "1925002086405832987",
        "in_reply_to_screen_name": "cline",
        "replyCount": 0,
        "quoteCount": 0,
        "repostCount": 0,
        "favouriteCount": 0,
        "viewsCount": "141",
        "conversationId": "1925002086405832987",
        "replyId": "1925061330698174664"
    }

def test_extract_tweet_text():
    """Test the extract_tweet_text function."""
    logger.info("Testing extract_tweet_text function...")
    
    # Create a mock tweet
    mock_tweet = create_mock_tweet()
    
    # Extract text from the mock tweet
    tweet_text = extract_tweet_text(mock_tweet)
    
    # Print the extracted text
    logger.info("Extracted tweet text:")
    logger.info(json.dumps(tweet_text, indent=2))
    
    # Verify the extraction - original fields
    assert tweet_text["tweet_id"] == "1925002086405832987"
    assert isinstance(tweet_text["author"], dict)  # Now author is a dict with details
    assert tweet_text["text"] == "This is a test tweet with #hashtag and @mention"
    assert tweet_text["timestamp"] == "Wed May 21 10:00:00 +0000 2025"
    assert tweet_text["urls"] == ["https://example.com"]
    assert tweet_text["hashtags"] == ["#hashtag"]
    assert tweet_text["mentions"] == ["@mention"]
    assert tweet_text["is_reply"] == False
    
    # Verify the extraction - new fields
    assert tweet_text["postUrl"] == "https://x.com/cline/status/1925002086405832987"
    assert tweet_text["postId"] == "1925002086405832987"
    assert tweet_text["replyId"] == "1925002086405832987"
    assert tweet_text["replyUrl"] == "https://x.com/cline/status/1925002086405832987"
    assert tweet_text["replyText"] == "This is a test tweet with #hashtag and @mention"
    assert tweet_text["conversationId"] == "1925002086405832987"
    assert len(tweet_text["media"]) > 0
    assert tweet_text["author"]["followersCount"] == 339
    assert tweet_text["author"]["favouritesCount"] == 39512
    assert tweet_text["author"]["friendsCount"] == 678
    assert "description" in tweet_text["author"]
    assert tweet_text["replyCount"] == 5
    assert tweet_text["quoteCount"] == 2
    assert tweet_text["repostCount"] == 10
    assert tweet_text["favouriteCount"] == 25
    assert tweet_text["viewsCount"] == "141"
    
    logger.info("extract_tweet_text test passed!")
    return tweet_text

def test_extract_thread_text():
    """Test the extract_thread_text function."""
    logger.info("Testing extract_thread_text function...")
    
    # Create mock tweet and replies
    mock_tweet = create_mock_tweet()
    mock_replies = [create_mock_reply()]
    
    # Extract text from the mock thread
    thread_text = extract_thread_text(mock_tweet, mock_replies)
    
    # Print the extracted thread text
    logger.info("Extracted thread text:")
    logger.info(json.dumps(thread_text, indent=2))
    
    # Verify the extraction - original fields
    assert len(thread_text) == 2
    assert thread_text[0]["tweet_id"] == "1925002086405832987"
    assert thread_text[1]["tweet_id"] == "1925061330698174664"
    assert thread_text[1]["is_reply"] == True
    assert thread_text[1]["reply_to"] == "cline"
    assert thread_text[1]["reply_to_id"] == "1925002086405832987"
    
    # Verify the extraction - new fields for reply
    assert thread_text[1]["postUrl"] == "https://x.com/cline/status/1925061330698174664"
    assert thread_text[1]["postId"] == "1925061330698174664"
    assert thread_text[1]["replyId"] == "1925061330698174664"
    assert thread_text[1]["replyUrl"] == "https://x.com/cline/status/1925061330698174664"
    assert thread_text[1]["replyText"] == "@cline Everyday I'm shocked and perturbed by how good + how quickly these updates come out"
    assert thread_text[1]["conversationId"] == "1925002086405832987"
    assert isinstance(thread_text[1]["author"], dict)
    assert thread_text[1]["replyCount"] == 0
    assert thread_text[1]["quoteCount"] == 0
    assert thread_text[1]["repostCount"] == 0
    assert thread_text[1]["favouriteCount"] == 0
    assert thread_text[1]["viewsCount"] == "141"
    
    logger.info("extract_thread_text test passed!")
    return thread_text

def test_save_thread_text():
    """Test the save_thread_text function."""
    logger.info("Testing save_thread_text function...")
    
    # Create a mock thread text
    thread_text = test_extract_thread_text()
    
    # Create a test output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the thread text
    output_path = save_thread_text(
        thread_text, 
        output_dir, 
        "cline", 
        "1925002086405832987"
    )
    
    # Verify the file was saved
    assert os.path.exists(output_path)
    
    # Read the saved file
    with open(output_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    # Verify the saved data
    assert len(saved_data) == 2
    assert saved_data[0]["tweet_id"] == "1925002086405832987"
    assert saved_data[1]["tweet_id"] == "1925061330698174664"
    
    logger.info(f"Thread text saved to: {output_path}")
    logger.info("save_thread_text test passed!")
    
    return output_path

def main():
    """Run all tests."""
    logger.info("Starting text extraction tests...")
    
    # Test extract_tweet_text
    test_extract_tweet_text()
    
    # Test extract_thread_text
    test_extract_thread_text()
    
    # Test save_thread_text
    output_path = test_save_thread_text()
    
    logger.info("All tests passed!")
    logger.info(f"Test output saved to: {output_path}")

if __name__ == "__main__":
    main()
