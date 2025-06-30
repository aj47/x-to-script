"""
Configuration settings for Google Gemini API and video analysis.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"

# Default model for video analysis
DEFAULT_VIDEO_MODEL = "gemini-1.5-pro"  # Best model for video analysis

# Alternative models for video analysis
AVAILABLE_VIDEO_MODELS = [
    "gemini-1.5-pro",      # Best for complex video analysis
    "gemini-1.5-flash",    # Faster, good for simple analysis
    "gemini-1.0-pro-vision"  # Legacy model with vision capabilities
]

# Video analysis settings
DEFAULT_ANALYSIS_DETAIL = "medium"  # Options: low, medium, high
MAX_VIDEO_SIZE_MB = 100  # Maximum video file size for analysis
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

# Analysis configuration
ANALYSIS_FEATURES = {
    "scene_description": True,      # Describe key scenes and visuals
    "text_extraction": True,        # Extract any text visible in video
    "object_detection": True,       # Identify objects and people
    "action_analysis": True,        # Describe actions and movements
    "mood_analysis": True,          # Analyze emotional tone and mood
    "visual_style": True,           # Describe visual style and aesthetics
    "content_summary": True         # Overall content summary
}

# Prompt templates for video analysis
SYSTEM_PROMPT = """You are an expert video content analyzer specializing in social media content. Your task is to analyze video content and provide detailed insights that will help create engaging TikTok scripts.

Focus on:
- Visual elements that would be important for script writing
- Key scenes and moments that could be highlighted
- Text or graphics visible in the video
- Overall mood and tone of the content
- Actions, gestures, or demonstrations shown
- Visual style and production quality

Provide structured, actionable insights that a content creator can use."""

VIDEO_ANALYSIS_PROMPT = """Analyze this video content and provide detailed insights for TikTok script creation with precise timestamps for video clipping.

Please analyze the following aspects:

1. **Scene Description**: Describe the key visual scenes and moments
2. **Text Content**: Extract any text, captions, or graphics visible in the video
3. **Visual Elements**: Identify important objects, people, settings, or demonstrations
4. **Actions & Movements**: Describe significant actions, gestures, or movements
5. **Mood & Tone**: Analyze the emotional tone and overall mood
6. **Visual Style**: Describe the production quality, lighting, colors, and aesthetic
7. **Content Summary**: Provide an overall summary of what the video shows
8. **Clippable Moments**: Identify specific segments perfect for TikTok clips with precise timestamps

IMPORTANT: Provide precise timestamps in MM:SS format (e.g., "01:23" for 1 minute 23 seconds) for all key moments. These will be used to automatically clip the video.

Respond in JSON format:
{
    "scene_description": "Detailed description of key visual scenes",
    "text_content": ["Any text visible in video"],
    "visual_elements": ["Key objects, people, settings"],
    "actions_movements": ["Significant actions or gestures"],
    "mood_tone": "Overall emotional tone and mood",
    "visual_style": "Production quality and aesthetic description",
    "content_summary": "Overall summary of video content",
    "script_suggestions": ["Specific suggestions for TikTok script integration"],
    "key_moments": [
        {
            "start_time": "MM:SS",
            "end_time": "MM:SS",
            "duration_seconds": number,
            "description": "what happens during this segment",
            "importance": "why this moment is significant for TikTok",
            "clip_type": "hook|intro|explainer|reaction|quote",
            "visual_focus": "what to focus on visually",
            "audio_highlight": "key audio/speech in this segment"
        }
    ],
    "best_clips_for_tiktok": [
        {
            "clip_name": "descriptive name for this clip",
            "start_time": "MM:SS",
            "end_time": "MM:SS",
            "duration_seconds": number,
            "why_perfect": "explanation of why this is perfect for TikTok",
            "suggested_use": "hook|intro|explainer|background|reaction",
            "visual_appeal": "what makes this visually engaging",
            "key_quote": "most important quote/speech in this clip"
        }
    ]
}"""

BATCH_ANALYSIS_PROMPT = """Analyze multiple video files from a Twitter/X thread and provide consolidated insights for TikTok script creation.

For each video, provide:
1. Individual analysis following the standard format
2. Cross-video connections and themes
3. Recommended script flow that incorporates multiple videos
4. Visual continuity suggestions

Focus on how the videos work together to tell a story or convey information."""

# Error messages
ERROR_NO_API_KEY = "No Gemini API key provided. Set it with --gemini-key, in a .env file, or as GEMINI_API_KEY environment variable."
ERROR_INVALID_MODEL = "Invalid Gemini model specified. Available models: {models}"
ERROR_VIDEO_TOO_LARGE = "Video file is too large for analysis. Maximum size: {max_size}MB"
ERROR_UNSUPPORTED_FORMAT = "Unsupported video format. Supported formats: {formats}"
ERROR_VIDEO_NOT_FOUND = "Video file not found: {path}"

# Analysis detail levels
ANALYSIS_DETAIL_LEVELS = {
    "low": {
        "description": "Basic analysis with essential information only",
        "max_tokens": 1000,
        "temperature": 0.3
    },
    "medium": {
        "description": "Balanced analysis with good detail",
        "max_tokens": 2000,
        "temperature": 0.5
    },
    "high": {
        "description": "Comprehensive analysis with maximum detail and precise timestamps",
        "max_tokens": 4000,
        "temperature": 0.7
    }
}

# Default settings for video analysis
DEFAULT_SETTINGS = {
    "model": DEFAULT_VIDEO_MODEL,
    "detail_level": DEFAULT_ANALYSIS_DETAIL,
    "include_timestamps": True,
    "extract_text": True,
    "analyze_mood": True,
    "suggest_script_integration": True
}
