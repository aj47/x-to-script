"""
TikTok Script Generator using OpenRouter API.

This module processes scraped Twitter/X thread content and generates
engaging TikTok video scripts with hooks, intros, and explainers.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import httpx
from openai import OpenAI

import config_openrouter

# Set up logging
logger = logging.getLogger('x-thread-dl.script_generator')

class ScriptGenerator:
    """Generates TikTok scripts from Twitter thread content using OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the script generator.

        Args:
            api_key: OpenRouter API key (defaults to config value)
            model: Model to use for generation (defaults to config value)
        """
        self.api_key = api_key or config_openrouter.OPENROUTER_API_KEY
        self.model = model or config_openrouter.DEFAULT_MODEL

        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable.")

        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=config_openrouter.OPENROUTER_BASE_URL
        )

        logger.info(f"Initialized ScriptGenerator with model: {self.model}")

    def load_thread_data(self, json_file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load thread data from a JSON file.

        Args:
            json_file_path: Path to the JSON file containing thread data

        Returns:
            List of tweet dictionaries or None if loading failed
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Loaded {len(data)} tweets from {json_file_path}")
            return data

        except Exception as e:
            logger.error(f"Error loading thread data from {json_file_path}: {str(e)}")
            return None

    def extract_thread_content(self, thread_data) -> str:
        """
        Extract and format thread content for script generation.

        Args:
            thread_data: Either a list of tweet dictionaries or a single tweet object

        Returns:
            Formatted string containing the thread content
        """
        if not thread_data:
            return ""

        content_parts = []

        # Handle both formats: list of tweets or single tweet object
        if isinstance(thread_data, dict):
            # Single tweet object (new format)
            tweets_to_process = [thread_data]
        elif isinstance(thread_data, list):
            # List of tweets (old format)
            tweets_to_process = thread_data
        else:
            logger.warning(f"Unexpected thread_data type: {type(thread_data)}")
            return ""

        for i, tweet in enumerate(tweets_to_process):
            # Handle different tweet formats
            if isinstance(tweet, str):
                # If tweet is a string, use it directly
                text = tweet.strip()
                author_name = 'Unknown'
                author_desc = ''
            elif isinstance(tweet, dict):
                # Extract text from various possible fields
                text = (
                    tweet.get('text', '') or
                    tweet.get('replyText', '') or
                    tweet.get('full_text', '') or
                    tweet.get('content', '') or
                    ''
                ).strip()

                # Extract author information
                author = tweet.get('author', {}) or tweet.get('user', {})
                if isinstance(author, dict):
                    author_name = (
                        author.get('username', '') or
                        author.get('screen_name', '') or
                        author.get('name', '') or
                        'Unknown'
                    )
                    author_desc = author.get('description', '')
                elif isinstance(author, str):
                    author_name = author
                    author_desc = ''
                else:
                    author_name = 'Unknown'
                    author_desc = ''
            else:
                logger.warning(f"Unexpected tweet format: {type(tweet)}")
                continue

            if not text:
                logger.warning(f"No text found in tweet {i+1}")
                continue

            # Format tweet content
            tweet_content = f"Tweet {i+1} by @{author_name}:\n{text}"

            if author_desc and i == 0:  # Add author description for first tweet
                tweet_content += f"\n(Author: {author_desc})"

            content_parts.append(tweet_content)

        return "\n\n---\n\n".join(content_parts)

    async def generate_script(self, thread_content: str) -> Optional[Dict[str, Any]]:
        """
        Generate a TikTok script from thread content using OpenRouter API.

        Args:
            thread_content: Formatted thread content string

        Returns:
            Dictionary containing the generated script or None if generation failed
        """
        try:
            prompt = config_openrouter.TIKTOK_SCRIPT_PROMPT.format(
                thread_content=thread_content
            )

            logger.info(f"Generating script using model: {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert TikTok content creator. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )

            script_text = response.choices[0].message.content.strip()

            # Parse the JSON response
            try:
                script_data = json.loads(script_text)
                logger.info("Successfully generated TikTok script")
                return script_data

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse script JSON: {e}")
                logger.debug(f"Raw response: {script_text}")
                return None

        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            return None

    def save_script(self, script_data: Dict[str, Any], output_path: str) -> bool:
        """
        Save generated script to a JSON file.

        Args:
            script_data: Generated script dictionary
            output_path: Path where to save the script

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Script saved to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving script to {output_path}: {str(e)}")
            return False

    async def process_thread_file(self, json_file_path: str, output_dir: str = None) -> Optional[str]:
        """
        Process a single thread JSON file and generate a TikTok script.

        Args:
            json_file_path: Path to the thread JSON file
            output_dir: Directory to save the generated script (defaults to config)

        Returns:
            Path to the generated script file or None if processing failed
        """
        # Load thread data
        thread_data = self.load_thread_data(json_file_path)
        if not thread_data:
            return None

        # Extract content
        thread_content = self.extract_thread_content(thread_data)
        if not thread_content.strip():
            logger.warning(f"No content extracted from {json_file_path}")
            return None

        # Generate script
        script_data = await self.generate_script(thread_content)
        if not script_data:
            return None

        # Determine output path
        if not output_dir:
            output_dir = config_openrouter.DEFAULT_SCRIPT_OUTPUT_DIR

        input_filename = Path(json_file_path).stem
        output_filename = f"{input_filename}_tiktok_script.json"
        output_path = os.path.join(output_dir, output_filename)

        # Save script
        if self.save_script(script_data, output_path):
            return output_path

        return None
