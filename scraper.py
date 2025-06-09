"""
Scraper module for the x-thread-dl tool.
Handles fetching tweets and replies using the Apify API.
"""

import asyncio
import re
import logging
from typing import Optional, Dict, List, Any, Union
from apify_client import ApifyClient

# Import configuration
import config

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.scraper')

class Scraper:
    """Class for scraping tweets and replies from X.com (Twitter)."""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the scraper with an Apify API token.
        
        Args:
            api_token (Optional[str]): The Apify API token. If None, uses the token from config.
        """
        self.api_token = api_token or config.APIFY_API_TOKEN
        if not self.api_token:
            logger.warning("No Apify API token provided. Scraping will likely fail.")
        
        # Initialize the Apify client
        self.client = ApifyClient(token=self.api_token)
    
    async def fetch_tweet(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a tweet using Apify's Twitter Scraper.
        
        Args:
            url (str): The X.com (Twitter) URL to scrape
            
        Returns:
            Optional[Dict[str, Any]]: The tweet data or None if scraping failed
        """
        try:
            logger.info(f"Fetching tweet from URL: {url}")
            
            # Extract tweet ID from URL
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                logger.error(f"Could not extract tweet ID from URL: {url}")
                return None
            
            # Ensure URL is properly formatted
            formatted_url = self._format_url(url)
            logger.info(f"Using formatted URL: {formatted_url}")
            
            # Prepare the input for the Twitter Scraper actor
            input_data = {
                "startUrls": [{"url": formatted_url}],
                "tweetsDesired": 1,
                "addUserInfo": True,
                "proxyConfig": {
                    "useApifyProxy": True
                }
            }
            
            # Use a separate thread for the blocking API call
            loop = asyncio.get_event_loop()
            run = await loop.run_in_executor(
                None,
                lambda: self.client.actor(config.TWITTER_SCRAPER_ACTOR_ID).call(run_input=input_data)
            )
            
            # Get the dataset items
            dataset_items = await loop.run_in_executor(
                None,
                lambda: self.client.dataset(run["defaultDatasetId"]).list_items().items
            )
            
            if not dataset_items:
                logger.warning(f"No tweet data found for URL: {url}")
                return None
            
            # Get the first (and should be only) item
            tweet_data = dataset_items[0]
            
            # Log success
            logger.info(f"Successfully fetched tweet from URL: {url}")
            
            return tweet_data
            
        except Exception as e:
            logger.error(f"Error fetching tweet from URL {url}: {str(e)}", exc_info=True)
            return None
    
    async def fetch_tweet_replies(self, url: str, limit: int = config.DEFAULT_REPLY_LIMIT) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch replies to a tweet using Apify's Twitter Replies Scraper.
        
        Args:
            url (str): The X.com (Twitter) URL to scrape replies from
            limit (int): Maximum number of replies to fetch
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of reply data or None if scraping failed
        """
        try:
            logger.info(f"Fetching up to {limit} tweet replies from URL: {url}")
            
            # Ensure URL is properly formatted
            formatted_url = self._format_url(url)
            logger.info(f"Using formatted URL for replies: {formatted_url}")
            
            # Prepare the input for the Twitter Replies Scraper actor
            input_data = {
                "postUrls": [formatted_url],
                "resultsLimit": limit
            }
            
            # Use a separate thread for the blocking API call
            loop = asyncio.get_event_loop()
            run = await loop.run_in_executor(
                None,
                lambda: self.client.actor(config.TWITTER_REPLIES_SCRAPER_ACTOR_ID).call(run_input=input_data)
            )
            
            # Get the dataset items
            dataset_items = await loop.run_in_executor(
                None,
                lambda: self.client.dataset(run["defaultDatasetId"]).list_items().items
            )
            
            if not dataset_items:
                logger.warning(f"No reply data found for URL: {url}")
                return []
            
            # Log success
            logger.info(f"Successfully fetched {len(dataset_items)} replies from URL: {url}")

            # Debug: Log the keys of each reply object to diagnose tweet ID extraction issues
            for i, reply in enumerate(dataset_items):
                logger.debug(f"Reply {i} keys: {list(reply.keys())}")
                # Debug: Log the full structure of the first reply to help diagnose author extraction issues
                if i == 0:
                    logger.debug(f"Reply 0 full structure: {reply}")

            return dataset_items
            
        except Exception as e:
            logger.error(f"Error fetching tweet replies from URL {url}: {str(e)}", exc_info=True)
            return None
    
    async def fetch_tweet_and_replies(self, url: str, reply_limit: int = config.DEFAULT_REPLY_LIMIT) -> Dict[str, Any]:
        """
        Fetch a tweet and its replies.
        
        Args:
            url (str): The X.com (Twitter) URL to scrape
            reply_limit (int): Maximum number of replies to fetch
            
        Returns:
            Dict[str, Any]: Dictionary containing the tweet and its replies
        """
        # Fetch the tweet
        tweet = await self.fetch_tweet(url)
        
        # Fetch the replies
        replies = await self.fetch_tweet_replies(url, reply_limit)
        
        return {
            "tweet": tweet,
            "replies": replies or []
        }
    
    def extract_video_url(self, tweet_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract the highest quality video URL from tweet data.

        Args:
            tweet_data (Dict[str, Any]): The tweet data

        Returns:
            Optional[str]: The highest quality video URL or None if no video exists
        """
        try:
            best_video_url = None
            best_bitrate = 0
            best_resolution = ""

            # First, check mediaDetails section (preferred as it has bitrate info)
            if 'mediaDetails' in tweet_data:
                for media in tweet_data['mediaDetails']:
                    if media.get('type') == 'video' and 'video_info' in media and 'variants' in media['video_info']:
                        variants = media['video_info']['variants']

                        # Filter for MP4 format and find highest bitrate
                        mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']

                        if mp4_variants:
                            # Sort by bitrate (highest first)
                            mp4_variants.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                            highest_quality = mp4_variants[0]

                            bitrate = highest_quality.get('bitrate', 0)
                            url = highest_quality.get('url')

                            if bitrate > best_bitrate and url:
                                best_bitrate = bitrate
                                best_video_url = url
                                # Extract resolution from URL if possible
                                if '/vid/avc1/' in url:
                                    resolution_part = url.split('/vid/avc1/')[1].split('/')[0]
                                    best_resolution = resolution_part

                                logger.info(f"Found high-quality video: {best_resolution} at {bitrate} bitrate")

            # If we found a good video in mediaDetails, return it
            if best_video_url and best_bitrate > 0:
                logger.info(f"Selected highest quality video: {best_resolution} ({best_bitrate} bitrate)")
                return best_video_url

            # Fallback: Check the video section (may not have bitrate info)
            if 'video' in tweet_data and tweet_data['video'] and 'variants' in tweet_data['video']:
                variants = tweet_data['video']['variants']

                # Prefer MP4 format
                mp4_variants = [v for v in variants if v.get('type') == 'video/mp4']

                if mp4_variants:
                    # Try to sort by resolution if bitrate is not available
                    # Look for resolution indicators in the src URL
                    def get_resolution_priority(variant):
                        src = variant.get('src', '')
                        if '3840x2160' in src:
                            return 4000  # 4K
                        elif '1920x1080' in src:
                            return 3000  # 1080p
                        elif '1280x720' in src:
                            return 2000  # 720p
                        elif '640x360' in src:
                            return 1000  # 360p
                        elif '480x270' in src:
                            return 500   # 270p
                        else:
                            return variant.get('bitrate', 0)  # Fallback to bitrate if available

                    mp4_variants.sort(key=get_resolution_priority, reverse=True)
                    selected_variant = mp4_variants[0]

                    src_url = selected_variant.get('src')
                    if src_url:
                        # Extract resolution info for logging
                        resolution_info = "unknown resolution"
                        if '/vid/avc1/' in src_url:
                            resolution_part = src_url.split('/vid/avc1/')[1].split('/')[0]
                            resolution_info = resolution_part

                        logger.info(f"Selected video from fallback method: {resolution_info}")
                        return src_url

                # If no MP4 variants, return the first variant's source
                if variants:
                    logger.warning("No MP4 variants found, using first available variant")
                    return variants[0].get('src')

            logger.warning("No video found in tweet data")
            return None

        except Exception as e:
            logger.error(f"Error extracting video URL from tweet data: {str(e)}", exc_info=True)
            return None
    
    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """
        Extract the tweet ID from an X.com (Twitter) URL.
        
        Args:
            url (str): The X.com (Twitter) URL
            
        Returns:
            Optional[str]: The tweet ID or None if extraction failed
        """
        try:
            # Pattern to match tweet IDs in X.com (Twitter) URLs
            pattern = r'(?:twitter\.com|x\.com)/\w+/status/(\d+)'
            match = re.search(pattern, url)
            
            if match:
                return match.group(1)
            
            # Log the URL and pattern when no match is found
            logger.debug(f"No tweet ID found in URL: {url} using pattern: {pattern}")
            
            return None
        except Exception as e:
            logger.error(f"Error extracting tweet ID from URL {url}: {str(e)}", exc_info=True)
            return None
    
    def _format_url(self, url: str) -> str:
        """
        Ensure URL is properly formatted.
        
        Args:
            url (str): The URL to format
            
        Returns:
            str: The formatted URL
        """
        if not url.startswith('http'):
            return f"https://{url}"
        return url
