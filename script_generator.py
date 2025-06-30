"""
TikTok script generator module for the x-thread-dl tool.
Generates TikTok video scripts from downloaded Twitter/X thread content using LLM analysis.
"""

import os
import json
import logging
import re
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
import config_gemini
from video_analyzer import VideoAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.script_generator')

# Suppress verbose logging from external libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
# Temporarily enable litellm debug logging to diagnose model prefix issue
logging.getLogger("litellm").setLevel(logging.INFO)

class ScriptGenerator:
    """
    Generates TikTok video scripts from Twitter/X thread content using LLM analysis.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = config_openrouter.DEFAULT_MODEL,
        enable_video_analysis: bool = False,
        gemini_api_key: Optional[str] = None,
        video_analysis_model: str = config_gemini.DEFAULT_VIDEO_MODEL
    ):
        """
        Initialize the script generator.

        Args:
            api_key (Optional[str]): OpenRouter API key
            model (str): LLM model to use for generation
            enable_video_analysis (bool): Whether to enable video analysis with Gemini
            gemini_api_key (Optional[str]): Gemini API key for video analysis
            video_analysis_model (str): Gemini model to use for video analysis
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
        self.enable_video_analysis = enable_video_analysis

        # Initialize video analyzer if enabled
        self.video_analyzer = None
        if enable_video_analysis:
            try:
                self.video_analyzer = VideoAnalyzer(
                    api_key=gemini_api_key,
                    model=video_analysis_model
                )
                logger.info(f"Video analysis enabled with model: {video_analysis_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize video analyzer: {str(e)}")
                logger.warning("Continuing without video analysis")
                self.enable_video_analysis = False

        # Configure environment for OpenRouter
        os.environ["OPENROUTER_API_KEY"] = self.api_key

        # Configure LiteLLM to handle free models gracefully
        # Disable cost calculation for free models to avoid pricing database errors
        if litellm:
            litellm.suppress_debug_info = True
            # Set custom pricing for free models to avoid lookup errors
            if ":free" in self.model:
                litellm.model_cost = {
                    f"openrouter/{self.model}": {
                        "input_cost_per_token": 0.0,
                        "output_cost_per_token": 0.0,
                        "max_tokens": 4096
                    }
                }

        logger.info(f"Initialized ScriptGenerator with model: {self.model}, video analysis: {self.enable_video_analysis}")
    
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

    def extract_tweet_metadata(self, thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from main thread tweet for visual content mapping.

        Args:
            thread_data (Dict[str, Any]): Thread data from parsed JSON

        Returns:
            Dict[str, Any]: Tweet metadata including ID, text, author, media info
        """
        try:
            tweet_metadata = {
                "tweet_id": thread_data.get('id_str', ''),
                "text": thread_data.get('text', ''),
                "author": {
                    "name": thread_data.get('user', {}).get('name', 'Unknown'),
                    "screen_name": thread_data.get('user', {}).get('screen_name', 'unknown'),
                    "profile_image": thread_data.get('user', {}).get('profile_image_url_https', '')
                },
                "media_count": len(thread_data.get('entities', {}).get('media', [])),
                "is_reply": False,
                "created_at": thread_data.get('created_at', ''),
                "favorite_count": thread_data.get('favorite_count', 0),
                "retweet_count": thread_data.get('retweet_count', 0)
            }

            return tweet_metadata

        except Exception as e:
            logger.error(f"Error extracting tweet metadata: {str(e)}", exc_info=True)
            return {}

    def extract_replies_metadata(self, replies_dir: Path) -> List[Dict[str, Any]]:
        """
        Extract metadata from all replies for visual content mapping.

        Args:
            replies_dir (Path): Path to the replies directory

        Returns:
            List[Dict[str, Any]]: List of reply metadata
        """
        try:
            replies_metadata = []

            if not replies_dir.exists():
                return replies_metadata

            # Process each reply
            for reply_dir in replies_dir.iterdir():
                if reply_dir.is_dir():
                    reply_file = reply_dir / "reply_text.json"
                    if reply_file.exists():
                        try:
                            with open(reply_file, 'r', encoding='utf-8') as f:
                                reply_data = json.load(f)

                            reply_metadata = {
                                "reply_id": reply_data.get('replyId', ''),
                                "tweet_id": reply_data.get('postId', ''),  # Original tweet ID
                                "text": reply_data.get('replyText', ''),
                                "author": {
                                    "name": reply_data.get('author', {}).get('name', 'Unknown'),
                                    "screen_name": reply_data.get('author', {}).get('screenName', 'unknown'),
                                    "followers_count": reply_data.get('author', {}).get('followersCount', 0)
                                },
                                "media_count": len(reply_data.get('media', [])),
                                "is_reply": True,
                                "timestamp": reply_data.get('timestamp', 0),
                                "favorite_count": reply_data.get('favouriteCount', 0),
                                "reply_count": reply_data.get('replyCount', 0)
                            }

                            replies_metadata.append(reply_metadata)

                        except Exception as e:
                            logger.warning(f"Error reading reply metadata {reply_file}: {str(e)}")
                            continue

            return replies_metadata

        except Exception as e:
            logger.error(f"Error extracting replies metadata: {str(e)}", exc_info=True)
            return []

    def create_visual_content_mapping(
        self,
        thread_metadata: Dict[str, Any],
        replies_metadata: List[Dict[str, Any]]
    ) -> str:
        """
        Create a formatted string with available tweet and reply data for the LLM prompt.

        Args:
            thread_metadata (Dict[str, Any]): Main thread metadata
            replies_metadata (List[Dict[str, Any]]): List of reply metadata

        Returns:
            str: Formatted content mapping for LLM processing
        """
        try:
            mapping_content = "\n\n=== AVAILABLE VISUAL CONTENT FOR CURATION ===\n\n"

            # Add main thread information
            if thread_metadata:
                mapping_content += f"MAIN THREAD:\n"
                mapping_content += f"- Tweet ID: {thread_metadata.get('tweet_id', 'N/A')}\n"
                mapping_content += f"- Author: {thread_metadata.get('author', {}).get('name', 'N/A')} (@{thread_metadata.get('author', {}).get('screen_name', 'N/A')})\n"
                mapping_content += f"- Text: {thread_metadata.get('text', 'N/A')[:200]}{'...' if len(thread_metadata.get('text', '')) > 200 else ''}\n"
                mapping_content += f"- Media Count: {thread_metadata.get('media_count', 0)}\n"
                mapping_content += f"- Engagement: {thread_metadata.get('favorite_count', 0)} likes, {thread_metadata.get('retweet_count', 0)} retweets\n\n"

            # Add replies information
            if replies_metadata:
                mapping_content += f"AVAILABLE REPLIES ({len(replies_metadata)} total):\n"
                for i, reply in enumerate(replies_metadata[:5], 1):  # Limit to top 5 replies for prompt
                    mapping_content += f"{i}. Reply ID: {reply.get('reply_id', 'N/A')}\n"
                    mapping_content += f"   Author: {reply.get('author', {}).get('name', 'N/A')} (@{reply.get('author', {}).get('screen_name', 'N/A')})\n"
                    mapping_content += f"   Text: {reply.get('text', 'N/A')[:150]}{'...' if len(reply.get('text', '')) > 150 else ''}\n"
                    mapping_content += f"   Engagement: {reply.get('favorite_count', 0)} likes, {reply.get('reply_count', 0)} replies\n"
                    mapping_content += f"   Followers: {reply.get('author', {}).get('followers_count', 0)}\n\n"

                if len(replies_metadata) > 5:
                    mapping_content += f"... and {len(replies_metadata) - 5} more replies available\n\n"

            mapping_content += "VISUAL CURATION INSTRUCTIONS:\n"
            mapping_content += "- Use specific Tweet IDs and Reply IDs in your visual_cues and visual_timeline\n"
            mapping_content += "- Select the most engaging and relevant content for visual display\n"
            mapping_content += "- Consider author credibility (follower count) when choosing replies to highlight\n"
            mapping_content += "- Time visual elements to sync with narration for maximum impact\n"
            mapping_content += "- Use different presentation styles (full_tweet, quote_style, text_only) strategically\n\n"

            return mapping_content

        except Exception as e:
            logger.error(f"Error creating visual content mapping: {str(e)}", exc_info=True)
            return ""

    def enhance_script_with_metadata(
        self,
        script_data: Dict[str, Any],
        thread_metadata: Dict[str, Any],
        replies_metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhance the generated script with additional metadata for visual content curation.

        Args:
            script_data (Dict[str, Any]): Generated script data
            thread_metadata (Dict[str, Any]): Main thread metadata
            replies_metadata (List[Dict[str, Any]]): List of reply metadata

        Returns:
            Dict[str, Any]: Enhanced script with additional metadata
        """
        try:
            if not script_data:
                return script_data

            # Add available tweets to source metadata
            available_tweets = []

            # Add main thread
            if thread_metadata:
                available_tweets.append({
                    "tweet_id": thread_metadata.get('tweet_id', ''),
                    "text": thread_metadata.get('text', ''),
                    "author": thread_metadata.get('author', {}).get('screen_name', ''),
                    "media_count": thread_metadata.get('media_count', 0),
                    "is_reply": False
                })

            # Add replies
            for reply in replies_metadata:
                available_tweets.append({
                    "tweet_id": reply.get('reply_id', ''),
                    "text": reply.get('text', ''),
                    "author": reply.get('author', {}).get('screen_name', ''),
                    "media_count": reply.get('media_count', 0),
                    "is_reply": True
                })

            # Update source metadata
            if "source_metadata" not in script_data:
                script_data["source_metadata"] = {}

            script_data["source_metadata"]["available_tweets"] = available_tweets

            # Add visual content analysis
            visual_analysis = self.analyze_visual_content_usage(script_data)
            script_data["source_metadata"]["visual_content_analysis"] = visual_analysis

            return script_data

        except Exception as e:
            logger.error(f"Error enhancing script with metadata: {str(e)}", exc_info=True)
            return script_data

    def analyze_visual_content_usage(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the visual content usage in the generated script.

        Args:
            script_data (Dict[str, Any]): Generated script data

        Returns:
            Dict[str, Any]: Visual content usage analysis
        """
        try:
            analysis = {
                "total_visual_elements": 0,
                "tweet_display_count": 0,
                "reply_highlight_count": 0,
                "text_overlay_count": 0,
                "transition_count": 0
            }

            # Analyze visual cues in each section
            for section_name in ["hook", "intro", "explainer"]:
                section = script_data.get(section_name, {})
                visual_cues = section.get("visual_cues", [])

                for cue in visual_cues:
                    analysis["total_visual_elements"] += 1
                    cue_type = cue.get("type", "")

                    if cue_type == "tweet_display":
                        analysis["tweet_display_count"] += 1
                    elif cue_type == "reply_highlight":
                        analysis["reply_highlight_count"] += 1
                    elif cue_type == "text_overlay":
                        analysis["text_overlay_count"] += 1
                    elif cue_type == "transition":
                        analysis["transition_count"] += 1

            # Analyze visual timeline if present
            visual_timeline = script_data.get("visual_timeline", {})
            timeline_events = visual_timeline.get("timeline_events", [])
            analysis["total_visual_elements"] += len(timeline_events)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing visual content usage: {str(e)}", exc_info=True)
            return {
                "total_visual_elements": 0,
                "tweet_display_count": 0,
                "reply_highlight_count": 0,
                "text_overlay_count": 0,
                "transition_count": 0
            }

    def validate_and_enhance_timing(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance timing specifications in the generated script.

        Args:
            script_data (Dict[str, Any]): Generated script data

        Returns:
            Dict[str, Any]: Script with validated and enhanced timing
        """
        try:
            if not script_data:
                return script_data

            total_duration = script_data.get("metadata", {}).get("total_duration", 60)
            current_timestamp = 0

            # Process each section and validate timing
            for section_name in ["hook", "intro", "explainer"]:
                section = script_data.get(section_name, {})
                section_duration = section.get("duration_seconds", 0)

                if section_duration <= 0:
                    logger.warning(f"Invalid duration for {section_name}, setting default")
                    if section_name == "hook":
                        section_duration = 15
                    elif section_name == "intro":
                        section_duration = 15
                    else:  # explainer
                        section_duration = 30
                    section["duration_seconds"] = section_duration

                # Validate and adjust visual cues timing
                visual_cues = section.get("visual_cues", [])
                for cue in visual_cues:
                    cue_timestamp = cue.get("timestamp", 0)
                    cue_duration = cue.get("duration", 3)

                    # Ensure timestamp is within section bounds
                    if cue_timestamp < current_timestamp:
                        cue["timestamp"] = current_timestamp
                    elif cue_timestamp >= current_timestamp + section_duration:
                        cue["timestamp"] = current_timestamp + section_duration - cue_duration

                    # Ensure duration doesn't exceed section bounds
                    max_duration = (current_timestamp + section_duration) - cue["timestamp"]
                    if cue_duration > max_duration:
                        cue["duration"] = max_duration

                current_timestamp += section_duration

            # Enhance or create visual timeline
            script_data = self.create_enhanced_visual_timeline(script_data, total_duration)

            return script_data

        except Exception as e:
            logger.error(f"Error validating and enhancing timing: {str(e)}", exc_info=True)
            return script_data

    def create_enhanced_visual_timeline(self, script_data: Dict[str, Any], total_duration: int) -> Dict[str, Any]:
        """
        Create or enhance the visual timeline based on section visual cues.

        Args:
            script_data (Dict[str, Any]): Generated script data
            total_duration (int): Total script duration

        Returns:
            Dict[str, Any]: Script with enhanced visual timeline
        """
        try:
            if "visual_timeline" not in script_data:
                script_data["visual_timeline"] = {
                    "total_duration": total_duration,
                    "timeline_events": [],
                    "tweet_references": {},
                    "visual_transitions": []
                }

            timeline_events = []
            tweet_references = {}
            visual_transitions = []
            current_timestamp = 0

            # Process each section to build timeline
            for section_name in ["hook", "intro", "explainer"]:
                section = script_data.get(section_name, {})
                section_duration = section.get("duration_seconds", 0)
                visual_cues = section.get("visual_cues", [])

                for cue in visual_cues:
                    # Create timeline event
                    event = {
                        "timestamp": current_timestamp + cue.get("timestamp", 0),
                        "duration": cue.get("duration", 3),
                        "visual_type": self.map_cue_type_to_visual_type(cue.get("type", "")),
                        "content": cue.get("content", ""),
                        "presentation_details": {
                            "animation_in": cue.get("presentation", {}).get("animation", "fade_in"),
                            "animation_out": "fade_out",
                            "position": cue.get("presentation", {}).get("position", "center"),
                            "size": "medium"
                        }
                    }

                    # Add tweet/reply references
                    if cue.get("tweet_id"):
                        event["tweet_id"] = cue["tweet_id"]
                        self.update_tweet_references(tweet_references, cue["tweet_id"], event["timestamp"])

                    if cue.get("reply_id"):
                        event["reply_id"] = cue["reply_id"]
                        self.update_tweet_references(tweet_references, cue["reply_id"], event["timestamp"])

                    # Add narration sync
                    event["sync_with_narration"] = {
                        "narration_text": section.get("text", "")[:100],
                        "timing_cue": "during_word"
                    }

                    timeline_events.append(event)

                # Add section transition
                if current_timestamp + section_duration < total_duration:
                    visual_transitions.append({
                        "from_timestamp": current_timestamp + section_duration - 1,
                        "to_timestamp": current_timestamp + section_duration + 1,
                        "transition_type": "fade",
                        "duration": 1,
                        "easing": "ease_in_out"
                    })

                current_timestamp += section_duration

            # Update visual timeline
            script_data["visual_timeline"]["timeline_events"] = timeline_events
            script_data["visual_timeline"]["tweet_references"] = tweet_references
            script_data["visual_timeline"]["visual_transitions"] = visual_transitions

            return script_data

        except Exception as e:
            logger.error(f"Error creating enhanced visual timeline: {str(e)}", exc_info=True)
            return script_data

    def map_cue_type_to_visual_type(self, cue_type: str) -> str:
        """
        Map visual cue type to visual timeline type.

        Args:
            cue_type (str): Visual cue type from section

        Returns:
            str: Corresponding visual timeline type
        """
        mapping = {
            "tweet_display": "main_tweet",
            "reply_highlight": "reply_tweet",
            "text_overlay": "text_overlay",
            "transition": "transition",
            "effect": "effect"
        }
        return mapping.get(cue_type, "text_overlay")

    def update_tweet_references(self, tweet_references: Dict[str, Any], tweet_id: str, timestamp: float):
        """
        Update tweet references tracking.

        Args:
            tweet_references (Dict[str, Any]): Tweet references dictionary
            tweet_id (str): Tweet or reply ID
            timestamp (float): Timestamp of usage
        """
        if tweet_id not in tweet_references:
            tweet_references[tweet_id] = {
                "usage_count": 0,
                "display_timestamps": [],
                "display_style": "full_tweet",
                "highlight_text": [],
                "author_focus": False,
                "media_included": False
            }

        tweet_references[tweet_id]["usage_count"] += 1
        tweet_references[tweet_id]["display_timestamps"].append(timestamp)

    def get_script_summary(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the script's visual content and timing.

        Args:
            script_data (Dict[str, Any]): Generated script data

        Returns:
            Dict[str, Any]: Script summary with key metrics
        """
        try:
            summary = {
                "total_duration": script_data.get("metadata", {}).get("total_duration", 0),
                "sections": {},
                "visual_elements": {
                    "total_count": 0,
                    "by_type": {},
                    "timeline_events": 0
                },
                "tweet_usage": {
                    "unique_tweets": 0,
                    "unique_replies": 0,
                    "total_references": 0
                },
                "complexity_score": "simple"
            }

            # Analyze sections
            for section_name in ["hook", "intro", "explainer"]:
                section = script_data.get(section_name, {})
                visual_cues = section.get("visual_cues", [])

                summary["sections"][section_name] = {
                    "duration": section.get("duration_seconds", 0),
                    "visual_cues_count": len(visual_cues),
                    "text_length": len(section.get("text", ""))
                }

                # Count visual elements by type
                for cue in visual_cues:
                    cue_type = cue.get("type", "unknown")
                    summary["visual_elements"]["by_type"][cue_type] = summary["visual_elements"]["by_type"].get(cue_type, 0) + 1
                    summary["visual_elements"]["total_count"] += 1

            # Analyze visual timeline
            visual_timeline = script_data.get("visual_timeline", {})
            timeline_events = visual_timeline.get("timeline_events", [])
            tweet_references = visual_timeline.get("tweet_references", {})

            summary["visual_elements"]["timeline_events"] = len(timeline_events)
            summary["tweet_usage"]["unique_tweets"] = len([ref for ref in tweet_references.keys() if not ref.startswith("reply_")])
            summary["tweet_usage"]["unique_replies"] = len([ref for ref in tweet_references.keys() if ref.startswith("reply_")])
            summary["tweet_usage"]["total_references"] = sum(ref.get("usage_count", 0) for ref in tweet_references.values())

            # Calculate complexity score
            total_visual_elements = summary["visual_elements"]["total_count"] + summary["visual_elements"]["timeline_events"]
            if total_visual_elements <= 5:
                summary["complexity_score"] = "simple"
            elif total_visual_elements <= 15:
                summary["complexity_score"] = "moderate"
            else:
                summary["complexity_score"] = "complex"

            return summary

        except Exception as e:
            logger.error(f"Error generating script summary: {str(e)}", exc_info=True)
            return {"error": "Failed to generate summary"}

    def export_visual_timeline_csv(self, script_data: Dict[str, Any], output_path: Path) -> bool:
        """
        Export the visual timeline to a CSV file for video editing software.

        Args:
            script_data (Dict[str, Any]): Generated script data
            output_path (Path): Output CSV file path

        Returns:
            bool: True if exported successfully
        """
        try:
            import csv

            visual_timeline = script_data.get("visual_timeline", {})
            timeline_events = visual_timeline.get("timeline_events", [])

            if not timeline_events:
                logger.warning("No timeline events to export")
                return False

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'duration', 'visual_type', 'content',
                    'tweet_id', 'reply_id', 'animation_in', 'animation_out',
                    'position', 'size', 'narration_sync'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for event in timeline_events:
                    presentation = event.get("presentation_details", {})
                    sync = event.get("sync_with_narration", {})

                    writer.writerow({
                        'timestamp': event.get('timestamp', 0),
                        'duration': event.get('duration', 0),
                        'visual_type': event.get('visual_type', ''),
                        'content': event.get('content', ''),
                        'tweet_id': event.get('tweet_id', ''),
                        'reply_id': event.get('reply_id', ''),
                        'animation_in': presentation.get('animation_in', ''),
                        'animation_out': presentation.get('animation_out', ''),
                        'position': presentation.get('position', ''),
                        'size': presentation.get('size', ''),
                        'narration_sync': sync.get('narration_text', '')[:50]
                    })

            logger.info(f"Visual timeline exported to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting visual timeline to CSV: {str(e)}", exc_info=True)
            return False

    def _format_video_analysis_for_prompt(self, video_analysis: Dict[str, Any]) -> str:
        """
        Format video analysis results for inclusion in the LLM prompt.

        Args:
            video_analysis (Dict[str, Any]): Video analysis results

        Returns:
            str: Formatted video context for the prompt
        """
        try:
            video_context = "VIDEO ANALYSIS CONTEXT:\n"

            # Add consolidated insights
            consolidated = video_analysis.get("consolidated_insights", {})
            if consolidated:
                video_context += "Overall Video Insights:\n"

                if consolidated.get("common_visual_elements"):
                    video_context += f"- Visual Elements: {', '.join(consolidated['common_visual_elements'])}\n"

                if consolidated.get("overall_mood_themes"):
                    video_context += f"- Mood/Tone: {', '.join(consolidated['overall_mood_themes'])}\n"

                if consolidated.get("extracted_text"):
                    video_context += f"- Text in Videos: {', '.join(consolidated['extracted_text'])}\n"

                if consolidated.get("key_actions"):
                    video_context += f"- Key Actions: {', '.join(consolidated['key_actions'])}\n"

                video_context += "\n"

            # Add script integration suggestions
            suggestions = video_analysis.get("script_integration_suggestions", [])
            if suggestions:
                video_context += "Script Integration Suggestions:\n"
                for suggestion in suggestions:
                    video_context += f"- {suggestion}\n"
                video_context += "\n"

            # Add key moments from individual analyses with precise timestamps
            individual_analyses = video_analysis.get("individual_analyses", {})
            if individual_analyses:
                video_context += "Key Video Moments with Timestamps:\n"
                for video_id, analysis in individual_analyses.items():
                    if "key_moments" in analysis and analysis["key_moments"]:
                        video_context += f"Video {video_id}:\n"
                        for moment in analysis["key_moments"][:4]:  # Include more moments for better coverage
                            start_time = moment.get('start_time', 'N/A')
                            end_time = moment.get('end_time', 'N/A')
                            description = moment.get('description', 'N/A')
                            importance = moment.get('importance', 'N/A')
                            clip_type = moment.get('clip_type', 'general')
                            audio_highlight = moment.get('audio_highlight', '')

                            video_context += f"  - TIMESTAMP {start_time}-{end_time}: {description}\n"
                            video_context += f"    * Importance: {importance}\n"
                            video_context += f"    * Best for: {clip_type}\n"
                            if audio_highlight:
                                video_context += f"    * Key quote: {audio_highlight}\n"
                            video_context += "\n"

                        # Add best clips section
                        if "best_clips_for_tiktok" in analysis and analysis["best_clips_for_tiktok"]:
                            video_context += f"  RECOMMENDED CLIPS for {video_id}:\n"
                            for clip in analysis["best_clips_for_tiktok"]:
                                clip_name = clip.get('clip_name', 'Unnamed')
                                start_time = clip.get('start_time', 'N/A')
                                end_time = clip.get('end_time', 'N/A')
                                suggested_use = clip.get('suggested_use', 'general')
                                key_quote = clip.get('key_quote', '')

                                video_context += f"    * {clip_name} ({start_time}-{end_time}) - Use for: {suggested_use}\n"
                                if key_quote:
                                    video_context += f"      Quote: {key_quote}\n"
                            video_context += "\n"

            return video_context.strip()

        except Exception as e:
            logger.error(f"Error formatting video analysis for prompt: {str(e)}", exc_info=True)
            return "VIDEO ANALYSIS: Error processing video context"

    async def generate_script(
        self,
        thread_content: str,
        style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
        target_duration: int = config_openrouter.DEFAULT_TARGET_DURATION,
        video_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a TikTok script from thread content using LLM.

        Args:
            thread_content (str): Formatted thread content
            style (str): Script style (engaging, educational, viral, professional)
            target_duration (int): Target duration in seconds
            video_analysis (Optional[Dict[str, Any]]): Video analysis results to include in context

        Returns:
            Optional[Dict[str, Any]]: Generated script data or None if failed
        """
        try:
            if style not in config_openrouter.SCRIPT_STYLES:
                raise ValueError(config_openrouter.ERROR_INVALID_STYLE)
            
            # Prepare the content with video analysis if available
            enhanced_content = thread_content
            if video_analysis and video_analysis.get("individual_analyses"):
                video_context = self._format_video_analysis_for_prompt(video_analysis)
                enhanced_content = f"{thread_content}\n\n{video_context}"

            # Try simplified prompt first for better compatibility
            use_simple_prompt = self.model.startswith("deepseek/") or "free" in self.model.lower()

            if use_simple_prompt:
                prompt = config_openrouter.SCRIPT_GENERATION_PROMPT_SIMPLE.format(
                    thread_content=enhanced_content,
                    target_duration=target_duration,
                    style=style
                )
                logger.info(f"Using simplified prompt for model {self.model}")
            else:
                prompt = config_openrouter.SCRIPT_GENERATION_PROMPT.format(
                    thread_content=enhanced_content,
                    target_duration=target_duration,
                    style=style
                )
                logger.info(f"Using full prompt for model {self.model}")

            # Define fallback models (prioritize free models)
            fallback_models = [
                self.model,  # Try the original model first
                "qwen/qwen-2.5-72b-instruct:free",
                "microsoft/phi-3-medium-4k-instruct:free",
                "deepseek/deepseek-r1-0528:free"  # Try deepseek again as last resort
            ]

            # Remove duplicates while preserving order
            seen = set()
            unique_fallback_models = []
            for model in fallback_models:
                if model not in seen:
                    seen.add(model)
                    unique_fallback_models.append(model)

            last_error = None
            response = None

            for attempt, model_to_try in enumerate(unique_fallback_models):
                try:
                    logger.info(f"Attempt {attempt + 1}/{len(unique_fallback_models)}: Generating script with model {model_to_try}, style: {style}")

                    # Make the LLM API call using OpenRouter via litellm
                    response = await asyncio.to_thread(
                        completion,
                        model=f"openrouter/{model_to_try}",  # Prefix with openrouter/ for litellm
                        messages=[
                            {"role": "system", "content": config_openrouter.SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000  # Increased token limit
                    )

                    # If we get here, the API call succeeded
                    logger.info(f"✅ Successfully generated script with model: {model_to_try}")
                    break

                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    logger.warning(f"❌ Model {model_to_try} failed: {error_msg}")

                    # Check if this is a 502 error or provider issue
                    if "502" in error_msg or "Bad Gateway" in error_msg or "Provider returned error" in error_msg:
                        logger.info(f"Provider issue detected for {model_to_try}, trying next model...")
                        continue
                    elif "rate limit" in error_msg.lower():
                        logger.info(f"Rate limit hit for {model_to_try}, trying next model...")
                        continue
                    elif attempt < len(unique_fallback_models) - 1:
                        logger.info(f"Error with {model_to_try}, trying next model...")
                        continue
                    else:
                        # Last attempt failed, re-raise the error
                        raise e

            if response is None:
                # All models failed
                logger.error("All fallback models failed")
                if last_error:
                    raise last_error
                else:
                    raise Exception("All models failed without specific error")
            
            # Extract the generated content
            generated_content = response.choices[0].message.content.strip()
            logger.debug(f"Raw generated content length: {len(generated_content)} characters")
            logger.debug(f"Raw content preview: {generated_content[:200]}...")

            # Try to parse as JSON
            try:
                script_data = json.loads(generated_content)
                logger.info("Successfully generated and parsed script")

                # Validate and enhance timing
                script_data = self.validate_and_enhance_timing(script_data)
                logger.info("Script timing validated and enhanced")

                return script_data
            except json.JSONDecodeError as e:
                # Try to extract JSON from the content if it's wrapped in other text
                logger.warning(f"Initial JSON parsing failed: {str(e)}")
                logger.warning("Attempting to extract JSON...")

                # Look for JSON content between curly braces
                import re
                json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        logger.debug(f"Extracted JSON content length: {len(json_content)} characters")
                        script_data = json.loads(json_content)
                        logger.info("Successfully extracted and parsed JSON from response")

                        # Validate and enhance timing
                        script_data = self.validate_and_enhance_timing(script_data)
                        logger.info("Extracted script timing validated and enhanced")

                        return script_data
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Extracted JSON also failed to parse: {str(e2)}")

                        # Try to fix common JSON syntax errors
                        try:
                            fixed_json = self._fix_common_json_errors(json_content)
                            if fixed_json != json_content:
                                logger.info("Attempting to parse JSON after fixing common syntax errors...")
                                script_data = json.loads(fixed_json)
                                logger.info("Successfully parsed JSON after fixing syntax errors")

                                # Validate and enhance timing
                                script_data = self.validate_and_enhance_timing(script_data)
                                logger.info("Fixed script timing validated and enhanced")

                                return script_data
                        except json.JSONDecodeError as e3:
                            logger.warning(f"JSON still failed to parse after fixes: {str(e3)}")

                # Log the problematic content for debugging
                logger.error(f"Failed to parse generated content as JSON. Content: {generated_content}")

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

    def _fix_common_json_errors(self, json_content: str) -> str:
        """
        Fix common JSON syntax errors that AI models make.

        Args:
            json_content (str): The potentially malformed JSON content

        Returns:
            str: JSON content with common errors fixed
        """
        try:
            # Fix missing quotes in hashtag arrays (common error)
            # Pattern: #word" -> "#word"
            json_content = re.sub(r'(\s+)#([a-zA-Z0-9_]+)"', r'\1"#\2"', json_content)

            # Fix hashtags missing # symbol in arrays (more targeted approach)
            # Find the hashtags array and fix items that don't start with #
            hashtag_pattern = r'"hashtags":\s*\[([\s\S]*?)\]'
            def fix_hashtags_in_array(match):
                hashtag_content = match.group(1)
                # Split by commas and fix each item
                items = re.findall(r'"([^"]*)"', hashtag_content)
                fixed_items = []
                for item in items:
                    if item and not item.startswith('#'):
                        fixed_items.append(f'"#{item}"')
                    else:
                        fixed_items.append(f'"{item}"')
                return f'"hashtags": [{", ".join(fixed_items)}]'

            json_content = re.sub(hashtag_pattern, fix_hashtags_in_array, json_content)

            # Fix trailing commas in arrays and objects
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)

            # Fix missing commas between array elements
            json_content = re.sub(r'"\s*\n\s*"', '",\n            "', json_content)

            logger.debug("Applied common JSON error fixes")
            return json_content

        except Exception as e:
            logger.warning(f"Error applying JSON fixes: {str(e)}")
            return json_content
    
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
            
            # Extract main thread text and metadata
            main_content = self.extract_thread_text(thread_data)
            if not main_content:
                logger.error("No text content found in thread")
                return None

            # Extract thread metadata for visual content mapping
            thread_metadata = self.extract_tweet_metadata(thread_data)

            # Extract replies if requested
            replies_content = ""
            replies_metadata = []
            if include_replies:
                replies_dir = thread_dir / "replies"
                replies_content = self.extract_replies_text(replies_dir)
                replies_metadata = self.extract_replies_metadata(replies_dir)

            # Create visual content mapping for LLM prompt
            visual_content_mapping = self.create_visual_content_mapping(thread_metadata, replies_metadata)

            # Combine content with visual mapping
            full_content = main_content
            if replies_content:
                full_content += f"\n\nReplies:\n{replies_content}"

            # Add visual content mapping to the prompt
            full_content += visual_content_mapping

            # Analyze videos if video analysis is enabled
            video_analysis = None
            if self.enable_video_analysis and self.video_analyzer:
                logger.info("Analyzing videos for enhanced script generation...")
                video_analysis = await self.video_analyzer.analyze_thread_videos(thread_dir)

                # Save video analysis results
                if video_analysis:
                    analysis_file = thread_dir / "video_analysis.json"
                    self.video_analyzer.save_analysis(video_analysis, analysis_file)

            # Generate script with video context
            script_data = await self.generate_script(full_content, style, target_duration, video_analysis)

            if script_data:
                # Add basic source metadata
                script_data["source_metadata"] = {
                    "thread_id": thread_data.get('id_str', 'unknown'),
                    "author": thread_data.get('user', {}).get('screen_name', 'unknown'),
                    "original_text": thread_data.get('text', ''),
                    "thread_directory": str(thread_dir),
                    "include_replies": include_replies,
                    "generation_style": style,
                    "target_duration": target_duration,
                    "video_analysis_enabled": self.enable_video_analysis,
                    "videos_analyzed": video_analysis.get("total_videos_analyzed", 0) if video_analysis else 0
                }

                # Enhance script with visual content metadata
                script_data = self.enhance_script_with_metadata(script_data, thread_metadata, replies_metadata)

                logger.info(f"Successfully processed thread with enhanced visual content: {thread_data.get('id_str', 'unknown')}")
            
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
