"""
Video analysis module for the x-thread-dl tool.
Uses Google Gemini API to analyze downloaded videos and extract visual context for TikTok script generation.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Gemini API integration
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

# Import local modules
import config_gemini

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.video_analyzer')

# Suppress verbose logging from external libraries
logging.getLogger("google.generativeai").setLevel(logging.WARNING)

class VideoAnalyzer:
    """
    Analyzes video content using Google Gemini API to extract visual context for script generation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = config_gemini.DEFAULT_VIDEO_MODEL):
        """
        Initialize the video analyzer.
        
        Args:
            api_key (Optional[str]): Gemini API key
            model (str): Gemini model to use for video analysis
        """
        if genai is None:
            raise ImportError("google-generativeai is required for video analysis. Install with: pip install google-generativeai")
        
        self.api_key = api_key or config_gemini.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(config_gemini.ERROR_NO_API_KEY)
        
        if model not in config_gemini.AVAILABLE_VIDEO_MODELS:
            raise ValueError(config_gemini.ERROR_INVALID_MODEL.format(
                models=", ".join(config_gemini.AVAILABLE_VIDEO_MODELS)
            ))
        
        self.model = model
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.gemini_model = genai.GenerativeModel(
            model_name=self.model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info(f"VideoAnalyzer initialized with model: {self.model}")
    
    def _validate_video_file(self, video_path: Path) -> bool:
        """
        Validate video file for analysis.
        
        Args:
            video_path (Path): Path to video file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not video_path.exists():
            logger.error(config_gemini.ERROR_VIDEO_NOT_FOUND.format(path=video_path))
            return False
        
        # Check file size
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb > config_gemini.MAX_VIDEO_SIZE_MB:
            logger.error(config_gemini.ERROR_VIDEO_TOO_LARGE.format(max_size=config_gemini.MAX_VIDEO_SIZE_MB))
            return False
        
        # Check file format
        if video_path.suffix.lower() not in config_gemini.SUPPORTED_VIDEO_FORMATS:
            logger.error(config_gemini.ERROR_UNSUPPORTED_FORMAT.format(
                formats=", ".join(config_gemini.SUPPORTED_VIDEO_FORMATS)
            ))
            return False
        
        return True
    
    async def analyze_video(
        self,
        video_path: Path,
        detail_level: str = config_gemini.DEFAULT_ANALYSIS_DETAIL
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single video file using Gemini API.
        
        Args:
            video_path (Path): Path to the video file
            detail_level (str): Analysis detail level (low, medium, high)
            
        Returns:
            Optional[Dict[str, Any]]: Analysis results or None if failed
        """
        try:
            if not self._validate_video_file(video_path):
                return None
            
            if detail_level not in config_gemini.ANALYSIS_DETAIL_LEVELS:
                detail_level = config_gemini.DEFAULT_ANALYSIS_DETAIL
            
            logger.info(f"Analyzing video: {video_path}")
            
            # Upload video file to Gemini
            video_file = genai.upload_file(path=str(video_path))
            logger.info(f"Video uploaded to Gemini: {video_file.name}")
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                logger.info("Video processing...")
                await asyncio.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                logger.error("Video processing failed")
                return None
            
            # Get analysis settings
            settings = config_gemini.ANALYSIS_DETAIL_LEVELS[detail_level]
            
            # Generate analysis
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                [video_file, config_gemini.VIDEO_ANALYSIS_PROMPT],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=settings["max_tokens"],
                    temperature=settings["temperature"]
                )
            )
            
            # Clean up uploaded file
            genai.delete_file(video_file.name)
            
            if not response.text:
                logger.error("No response from Gemini API")
                return None
            
            # Parse JSON response (handle markdown-wrapped JSON)
            try:
                analysis_data = self._extract_json_from_response(response.text)

                if not analysis_data:
                    logger.error("Could not extract valid JSON from Gemini response")
                    logger.debug(f"Raw response: {response.text}")
                    return None

                # Add metadata
                analysis_data["analysis_metadata"] = {
                    "video_path": str(video_path),
                    "file_size_mb": round(video_path.stat().st_size / (1024 * 1024), 2),
                    "model_used": self.model,
                    "detail_level": detail_level,
                    "analysis_timestamp": asyncio.get_event_loop().time()
                }

                logger.info(f"Successfully analyzed video: {video_path.name}")
                return analysis_data

            except Exception as e:
                logger.error(f"Failed to parse Gemini response: {str(e)}")
                logger.debug(f"Raw response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing video {video_path}: {str(e)}", exc_info=True)
            return None
    
    async def analyze_thread_videos(
        self,
        thread_dir: Path,
        detail_level: str = config_gemini.DEFAULT_ANALYSIS_DETAIL
    ) -> Dict[str, Any]:
        """
        Analyze all videos in a thread directory.
        
        Args:
            thread_dir (Path): Path to thread directory
            detail_level (str): Analysis detail level
            
        Returns:
            Dict[str, Any]: Combined analysis results for all videos
        """
        try:
            logger.info(f"Analyzing videos in thread directory: {thread_dir}")
            
            video_analyses = {}
            
            # Analyze main thread videos
            main_videos_dir = thread_dir / "videos"
            if main_videos_dir.exists():
                for video_file in main_videos_dir.glob("*.mp4"):
                    analysis = await self.analyze_video(video_file, detail_level)
                    if analysis:
                        video_analyses[f"main_{video_file.stem}"] = analysis
            
            # Analyze reply videos
            replies_dir = thread_dir / "replies"
            if replies_dir.exists():
                for reply_dir in replies_dir.iterdir():
                    if reply_dir.is_dir():
                        reply_videos_dir = reply_dir / "videos"
                        if reply_videos_dir.exists():
                            for video_file in reply_videos_dir.glob("*.mp4"):
                                analysis = await self.analyze_video(video_file, detail_level)
                                if analysis:
                                    video_analyses[f"reply_{reply_dir.name}_{video_file.stem}"] = analysis
            
            # Create consolidated analysis
            consolidated_analysis = {
                "thread_directory": str(thread_dir),
                "total_videos_analyzed": len(video_analyses),
                "individual_analyses": video_analyses,
                "consolidated_insights": self._consolidate_analyses(video_analyses),
                "script_integration_suggestions": self._generate_script_suggestions(video_analyses)
            }
            
            logger.info(f"Analyzed {len(video_analyses)} videos in thread")
            return consolidated_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing thread videos: {str(e)}", exc_info=True)
            return {}
    
    def _consolidate_analyses(self, video_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidate multiple video analyses into unified insights.
        
        Args:
            video_analyses (Dict[str, Any]): Individual video analyses
            
        Returns:
            Dict[str, Any]: Consolidated insights
        """
        if not video_analyses:
            return {}
        
        # Extract common themes and elements
        all_visual_elements = []
        all_moods = []
        all_text_content = []
        all_actions = []
        
        for analysis in video_analyses.values():
            if "visual_elements" in analysis:
                all_visual_elements.extend(analysis["visual_elements"])
            if "mood_tone" in analysis:
                all_moods.append(analysis["mood_tone"])
            if "text_content" in analysis:
                all_text_content.extend(analysis["text_content"])
            if "actions_movements" in analysis:
                all_actions.extend(analysis["actions_movements"])
        
        return {
            "common_visual_elements": list(set(all_visual_elements)),
            "overall_mood_themes": list(set(all_moods)),
            "extracted_text": list(set(all_text_content)),
            "key_actions": list(set(all_actions)),
            "video_count": len(video_analyses)
        }
    
    def _generate_script_suggestions(self, video_analyses: Dict[str, Any]) -> List[str]:
        """
        Generate script integration suggestions based on video analyses.
        
        Args:
            video_analyses (Dict[str, Any]): Individual video analyses
            
        Returns:
            List[str]: Script integration suggestions
        """
        suggestions = []
        
        if not video_analyses:
            return suggestions
        
        # Add suggestions based on analysis content
        suggestions.append("Reference key visual moments from the videos to create engaging hooks")
        suggestions.append("Use video content to support and illustrate main talking points")
        
        # Check for text content
        has_text = any("text_content" in analysis and analysis["text_content"] 
                      for analysis in video_analyses.values())
        if has_text:
            suggestions.append("Incorporate visible text/graphics from videos into script narration")
        
        # Check for demonstrations or actions
        has_actions = any("actions_movements" in analysis and analysis["actions_movements"] 
                         for analysis in video_analyses.values())
        if has_actions:
            suggestions.append("Highlight key actions or demonstrations shown in the videos")
        
        return suggestions
    
    def save_analysis(self, analysis_data: Dict[str, Any], output_path: Path) -> bool:
        """
        Save video analysis results to a JSON file.
        
        Args:
            analysis_data (Dict[str, Any]): Analysis results
            output_path (Path): Output file path
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Video analysis saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis to {output_path}: {str(e)}", exc_info=True)
            return False

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from a response that might be wrapped in markdown code blocks.

        Args:
            response_text (str): Raw response text from Gemini

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if parsing fails
        """
        import re

        # First try to parse as direct JSON
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        # Look for ```json ... ``` or ``` ... ``` patterns
        json_patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json ... ```
            r'```\s*\n(.*?)\n```',     # ``` ... ```
            r'```json(.*?)```',        # ```json...``` (no newlines)
            r'```(.*?)```'             # ```...``` (no newlines)
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the extracted text
                    json_text = match.strip()
                    if json_text:
                        return json.loads(json_text)
                except json.JSONDecodeError:
                    continue

        # Try to find JSON-like content between { and }
        try:
            # Find the first { and last } to extract potential JSON
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_text = response_text[start:end+1]
                return json.loads(json_text)
        except json.JSONDecodeError:
            pass

        # Try to extract partial JSON and fix common issues
        try:
            start = response_text.find('{')
            if start != -1:
                # Find the end of the JSON, even if incomplete
                json_text = response_text[start:]

                # Try to fix incomplete JSON by adding missing closing braces
                open_braces = json_text.count('{')
                close_braces = json_text.count('}')

                if open_braces > close_braces:
                    # Add missing closing braces
                    missing_braces = open_braces - close_braces
                    json_text += '}' * missing_braces

                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        pass

                # Try to extract just the complete parts
                lines = json_text.split('\n')
                for i in range(len(lines), 0, -1):
                    partial_json = '\n'.join(lines[:i])
                    if partial_json.count('{') == partial_json.count('}'):
                        try:
                            return json.loads(partial_json)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        logger.warning("Could not extract JSON from response using any method")
        return None
