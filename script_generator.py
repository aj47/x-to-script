"""
TikTok script generator module for the x-thread-dl tool.
Generates TikTok video scripts from downloaded Twitter/X thread content using LLM analysis.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import asyncio

# LLM integration
try:
    import litellm
    from litellm import completion
except ImportError:
    litellm = None
    completion = None

# Import local modules
import config_openrouter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.script_generator')

# Suppress verbose logging from external libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)

class ScriptGenerator:
    """
    Generates TikTok video scripts from Twitter/X thread content using LLM analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = config_openrouter.DEFAULT_MODEL):
        """
        Initialize the script generator.
        
        Args:
            api_key (Optional[str]): OpenRouter API key
            model (str): LLM model to use for generation
        """
        if litellm is None:
            raise ImportError("litellm is required for script generation. Install with: pip install litellm")
        
        self.api_key = api_key or config_openrouter.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError(config_openrouter.ERROR_NO_API_KEY)
        
        if model not in config_openrouter.AVAILABLE_MODELS:
            raise ValueError(config_openrouter.ERROR_INVALID_MODEL.format(
                models=", ".join(config_openrouter.AVAILABLE_MODELS)
            ))
        
        self.model = model

        # Configure environment for OpenRouter
        os.environ["OPENROUTER_API_KEY"] = self.api_key

        logger.info(f"Initialized ScriptGenerator with model: {self.model}")
    
    def extract_thread_text(self, thread_data: Dict[str, Any]) -> str:
        """
        Extract and format text content from thread data for LLM processing.
        
        Args:
            thread_data (Dict[str, Any]): Thread data from parsed JSON
            
        Returns:
            str: Formatted text content
        """
        try:
            # Extract main thread text
            main_text = thread_data.get('text', '')
            if not main_text:
                # Try alternative field names
                main_text = (
                    thread_data.get('full_text', '') or
                    thread_data.get('content', '') or
                    thread_data.get('tweet_text', '')
                )
            
            # Extract author info
            author_info = thread_data.get('user', {})
            author_name = author_info.get('name', 'Unknown')
            author_handle = author_info.get('screen_name', 'unknown')
            
            # Format the content
            formatted_content = f"Original Tweet by {author_name} (@{author_handle}):\n{main_text}\n\n"
            
            return formatted_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting thread text: {str(e)}", exc_info=True)
            return ""
    
    def extract_replies_text(self, replies_dir: Path) -> str:
        """
        Extract text content from all replies in a thread.
        
        Args:
            replies_dir (Path): Path to the replies directory
            
        Returns:
            str: Formatted replies text
        """
        try:
            replies_text = ""
            
            if not replies_dir.exists():
                return replies_text
            
            # Process each reply
            for reply_dir in replies_dir.iterdir():
                if reply_dir.is_dir():
                    reply_file = reply_dir / "reply_text.json"
                    if reply_file.exists():
                        try:
                            with open(reply_file, 'r', encoding='utf-8') as f:
                                reply_data = json.load(f)
                            
                            reply_text = reply_data.get('replyText', '')
                            author_info = reply_data.get('author', {})
                            author_name = author_info.get('name', 'Unknown')
                            author_handle = author_info.get('screenName', 'unknown')
                            
                            if reply_text:
                                replies_text += f"Reply by {author_name} (@{author_handle}):\n{reply_text}\n\n"
                                
                        except Exception as e:
                            logger.warning(f"Error reading reply file {reply_file}: {str(e)}")
                            continue
            
            return replies_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting replies text: {str(e)}", exc_info=True)
            return ""
    
    async def generate_script(
        self,
        thread_content: str,
        style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
        target_duration: int = config_openrouter.DEFAULT_TARGET_DURATION
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a TikTok script from thread content using LLM.
        
        Args:
            thread_content (str): Formatted thread content
            style (str): Script style (engaging, educational, viral, professional)
            target_duration (int): Target duration in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Generated script data or None if failed
        """
        try:
            if style not in config_openrouter.SCRIPT_STYLES:
                raise ValueError(config_openrouter.ERROR_INVALID_STYLE)
            
            # Prepare the prompt
            prompt = config_openrouter.SCRIPT_GENERATION_PROMPT.format(
                thread_content=thread_content,
                target_duration=target_duration,
                style=style
            )
            
            logger.info(f"Generating script with model {self.model}, style: {style}")

            # Make the LLM API call using OpenRouter via litellm
            response = await asyncio.to_thread(
                completion,
                model=f"openrouter/{self.model}",  # Prefix with openrouter/ for litellm
                messages=[
                    {"role": "system", "content": config_openrouter.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the generated content
            generated_content = response.choices[0].message.content.strip()

            # Try to parse as JSON
            try:
                script_data = json.loads(generated_content)
                logger.info("Successfully generated and parsed script")
                return script_data
            except json.JSONDecodeError:
                # Try to extract JSON from the content if it's wrapped in other text
                logger.warning("Initial JSON parsing failed, attempting to extract JSON...")

                # Look for JSON content between curly braces
                import re
                json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        script_data = json.loads(json_content)
                        logger.info("Successfully extracted and parsed JSON from response")
                        return script_data
                    except json.JSONDecodeError:
                        pass

                # If still can't parse, create a basic structure with the content
                logger.warning("Could not parse as JSON, creating basic structure")
                return {
                    "hook": {
                        "text": "Generated content could not be parsed as JSON",
                        "duration_seconds": 15,
                        "visual_suggestions": ["Check raw content below"]
                    },
                    "intro": {
                        "text": "Please review the raw generated content",
                        "duration_seconds": 15,
                        "visual_suggestions": ["Manual formatting needed"]
                    },
                    "explainer": {
                        "text": "The AI generated content but not in expected format",
                        "duration_seconds": 30,
                        "visual_suggestions": ["Review and reformat manually"]
                    },
                    "metadata": {
                        "total_duration": target_duration,
                        "style": style,
                        "key_points": ["JSON parsing failed"],
                        "hashtags": ["#error", "#manual_review_needed"],
                        "raw_content": generated_content,
                        "error": "Generated content was not in expected JSON format"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}", exc_info=True)
            return None
    
    async def process_thread_directory(
        self,
        thread_dir: Path,
        style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
        target_duration: int = config_openrouter.DEFAULT_TARGET_DURATION,
        include_replies: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Process a complete thread directory and generate a script.
        
        Args:
            thread_dir (Path): Path to thread directory
            style (str): Script style
            target_duration (int): Target duration in seconds
            include_replies (bool): Whether to include replies in analysis
            
        Returns:
            Optional[Dict[str, Any]]: Generated script with metadata
        """
        try:
            logger.info(f"Processing thread directory: {thread_dir}")
            
            # Read main thread content
            thread_file = thread_dir / "thread_text.json"
            if not thread_file.exists():
                logger.error(f"Thread text file not found: {thread_file}")
                return None
            
            with open(thread_file, 'r', encoding='utf-8') as f:
                thread_data = json.load(f)
            
            # Extract main thread text
            main_content = self.extract_thread_text(thread_data)
            if not main_content:
                logger.error("No text content found in thread")
                return None
            
            # Extract replies if requested
            replies_content = ""
            if include_replies:
                replies_dir = thread_dir / "replies"
                replies_content = self.extract_replies_text(replies_dir)
            
            # Combine content
            full_content = main_content
            if replies_content:
                full_content += f"\n\nReplies:\n{replies_content}"
            
            # Generate script
            script_data = await self.generate_script(full_content, style, target_duration)
            
            if script_data:
                # Add source metadata
                script_data["source_metadata"] = {
                    "thread_id": thread_data.get('id_str', 'unknown'),
                    "author": thread_data.get('user', {}).get('screen_name', 'unknown'),
                    "original_text": thread_data.get('text', ''),
                    "thread_directory": str(thread_dir),
                    "include_replies": include_replies,
                    "generation_style": style,
                    "target_duration": target_duration
                }
                
                logger.info(f"Successfully processed thread: {thread_data.get('id_str', 'unknown')}")
            
            return script_data
            
        except Exception as e:
            logger.error(f"Error processing thread directory {thread_dir}: {str(e)}", exc_info=True)
            return None
    
    def save_script(self, script_data: Dict[str, Any], output_path: Path) -> bool:
        """
        Save generated script to file.
        
        Args:
            script_data (Dict[str, Any]): Generated script data
            output_path (Path): Output file path
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving script to {output_path}: {str(e)}", exc_info=True)
            return False
