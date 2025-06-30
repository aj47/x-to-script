"""
Configuration settings for OpenRouter API and script generation.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default LLM model for script generation (free model)
DEFAULT_MODEL = "deepseek/deepseek-r1-0528:free"

# Alternative models (users can choose)
AVAILABLE_MODELS = [
    "deepseek/deepseek-r1-0528:free",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
    "google/gemini-pro-1.5",
    "qwen/qwen-2.5-72b-instruct:free",
    "microsoft/phi-3-medium-4k-instruct:free"
]

# Script generation settings
DEFAULT_SCRIPT_STYLE = "engaging"  # Options: engaging, educational, viral, professional
DEFAULT_TARGET_DURATION = 60  # Target duration in seconds for TikTok videos
DEFAULT_HOOK_LENGTH = 15  # Target hook length in seconds
DEFAULT_INTRO_LENGTH = 15  # Target intro length in seconds
DEFAULT_EXPLAINER_LENGTH = 30  # Target explainer length in seconds

# Output settings
SCRIPT_OUTPUT_FORMAT = "json"  # Options: json, markdown, txt
INCLUDE_METADATA = True  # Include source thread info in output

# Visual content curation settings
ENABLE_VISUAL_CURATION = True  # Enable enhanced visual content curation
MAX_VISUAL_ELEMENTS_PER_SECTION = 5  # Maximum visual elements per script section
DEFAULT_VISUAL_ELEMENT_DURATION = 3  # Default duration for visual elements in seconds
ENABLE_TIMELINE_EXPORT = True  # Enable CSV timeline export for video editing

# Visual presentation settings
VISUAL_ANIMATION_TYPES = [
    "fade_in", "slide_up", "zoom_in", "typewriter", "highlight", "none"
]
VISUAL_POSITIONS = [
    "center", "top", "bottom", "left", "right", "overlay"
]
VISUAL_STYLES = [
    "full_tweet", "text_only", "quote_style", "highlighted_text", "profile_focus"
]
VISUAL_EMPHASIS_TYPES = [
    "normal", "bold", "glow", "shake", "pulse"
]

# Timeline settings
ENABLE_AUTOMATIC_TRANSITIONS = True  # Automatically add transitions between sections
DEFAULT_TRANSITION_DURATION = 1  # Default transition duration in seconds
TRANSITION_TYPES = [
    "fade", "slide", "zoom", "wipe", "dissolve", "cut"
]

# Tweet selection criteria
MAX_REPLIES_FOR_VISUAL_CURATION = 5  # Maximum replies to consider for visual display
MIN_REPLY_ENGAGEMENT_THRESHOLD = 1  # Minimum likes/replies for reply consideration
PRIORITIZE_VERIFIED_AUTHORS = True  # Prioritize verified authors in reply selection

# Prompt templates
SYSTEM_PROMPT = """You are an expert TikTok content creator and script writer with advanced visual content curation skills. Your task is to analyze Twitter/X thread content and create comprehensive TikTok video scripts with detailed visual direction.

You specialize in creating viral, attention-grabbing content that follows TikTok best practices:
- Strong hooks that grab attention in the first 3 seconds
- Clear, concise explanations that are easy to follow
- Engaging storytelling that keeps viewers watching
- Proper pacing for short-form video content
- Strategic visual content selection and timing
- Synchronized narration and visual elements

VISUAL CONTENT EXPERTISE:
- You can identify which specific tweets from a thread should be displayed visually
- You understand how to time visual elements with narration for maximum impact
- You know how to highlight key reply tweets that add value to the story
- You can specify visual presentation styles (full tweet, text-only, quote style, etc.)
- You create detailed timestamp-based visual timelines

Always structure your scripts with three distinct sections:
1. HOOK: An attention-grabbing opening (10-15 seconds) with synchronized visuals
2. INTRO: Brief context and setup (10-15 seconds) with supporting visual content
3. EXPLAINER: Main content breakdown (30-40 seconds) with detailed visual curation

For each section, you must specify:
- Exact timing for when visual elements should appear
- Which specific tweets/replies to display and how
- Visual presentation style and animations
- Synchronization with narration timing

Keep the total script length appropriate for TikTok (45-60 seconds when spoken)."""

# Simplified prompt for better model compatibility
SCRIPT_GENERATION_PROMPT_SIMPLE = """Create a TikTok script from this Twitter thread content.

Thread Content:
{thread_content}

VISUAL CONTENT INSTRUCTIONS:
- When video analysis is provided with timestamps, USE SPECIFIC TIMESTAMPS in your visual suggestions
- Reference exact video moments like "00:05-00:09: Show Sutskever saying 'warm feelings' quote"
- Include specific tweet IDs and reply IDs when referencing visual content
- Time visual elements to sync with narration for maximum impact
- Use different presentation styles (full_tweet, quote_style, text_only) strategically

Requirements:
- Target duration: {target_duration} seconds
- Style: {style}
- Create 3 sections: Hook (15s), Intro (15s), Explainer (30s)
- Make it engaging for TikTok audience

IMPORTANT: Respond with ONLY valid JSON in this exact format:

{{
    "hook": {{
        "text": "Your hook text here",
        "duration_seconds": 15,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "intro": {{
        "text": "Your intro text here",
        "duration_seconds": 15,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "explainer": {{
        "text": "Your explainer text here",
        "duration_seconds": 30,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "metadata": {{
        "total_duration": {target_duration},
        "style": "{style}",
        "key_points": ["point 1", "point 2", "point 3"],
        "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
    }}
}}"""

# Keep the complex prompt as an alternative
SCRIPT_GENERATION_PROMPT = """Analyze the following Twitter/X thread content and create a comprehensive TikTok video script with detailed visual content curation.

Thread Content:
{thread_content}

VISUAL CONTENT CURATION REQUIREMENTS:
- Identify specific tweets from the thread that should be displayed visually
- Specify which reply tweets to highlight and quote
- Determine timing for when each visual element should appear
- Map visual content to specific moments in the narration
- Include detailed presentation instructions for each visual element

SCRIPT REQUIREMENTS:
- Target duration: {target_duration} seconds
- Style: {style}
- Create three sections: Hook, Intro, Explainer
- Make it engaging and suitable for TikTok audience
- Synchronize visual elements with narration timing
- Reference specific tweet IDs and reply IDs when applicable
- Include detailed visual timeline with timestamps

IMPORTANT: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

ENHANCED JSON FORMAT WITH VISUAL CURATION:
{{
    "hook": {{
        "text": "Hook content here",
        "duration_seconds": 15,
        "visual_cues": [
            {{
                "timestamp": 0,
                "duration": 3,
                "type": "tweet_display",
                "content": "Display main tweet",
                "tweet_id": "TWEET_ID_HERE",
                "presentation": {{
                    "animation": "fade_in",
                    "position": "center",
                    "style": "full_tweet",
                    "emphasis": "normal"
                }}
            }}
        ]
    }},
    "intro": {{
        "text": "Intro content here",
        "duration_seconds": 15,
        "visual_cues": [
            {{
                "timestamp": 15,
                "duration": 5,
                "type": "reply_highlight",
                "content": "Show key reply",
                "reply_id": "REPLY_ID_HERE",
                "presentation": {{
                    "animation": "slide_up",
                    "position": "bottom",
                    "style": "quote_style",
                    "emphasis": "bold"
                }}
            }}
        ]
    }},
    "explainer": {{
        "text": "Main explainer content here",
        "duration_seconds": 30,
        "visual_cues": [
            {{
                "timestamp": 30,
                "duration": 8,
                "type": "text_overlay",
                "content": "Key statistics or quotes",
                "presentation": {{
                    "animation": "typewriter",
                    "position": "overlay",
                    "style": "highlighted_text",
                    "emphasis": "glow"
                }}
            }}
        ]
    }},
    "visual_timeline": {{
        "total_duration": {target_duration},
        "timeline_events": [
            {{
                "timestamp": 0,
                "duration": 5,
                "visual_type": "main_tweet",
                "content": "Original thread tweet",
                "tweet_id": "MAIN_TWEET_ID",
                "presentation_details": {{
                    "animation_in": "fade_in",
                    "animation_out": "fade_out",
                    "position": "center",
                    "size": "large"
                }},
                "sync_with_narration": {{
                    "narration_text": "Specific part of hook this syncs with",
                    "emphasis_words": ["key", "words"],
                    "timing_cue": "during_word"
                }}
            }}
        ],
        "tweet_references": {{
            "TWEET_ID_1": {{
                "usage_count": 2,
                "display_timestamps": [0, 25],
                "display_style": "full_tweet",
                "highlight_text": ["important phrase"],
                "author_focus": true,
                "media_included": false
            }}
        }},
        "visual_transitions": [
            {{
                "from_timestamp": 14,
                "to_timestamp": 16,
                "transition_type": "fade",
                "duration": 1,
                "easing": "ease_in_out"
            }}
        ]
    }},
    "metadata": {{
        "total_duration": {target_duration},
        "style": "{style}",
        "key_points": ["point 1", "point 2", "point 3"],
        "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
        "visual_complexity": "moderate",
        "recommended_editing_software": ["CapCut", "Adobe Premiere"],
        "production_notes": ["Ensure tweet text is readable", "Use consistent branding"],
        "accessibility_features": {{
            "captions_required": true,
            "high_contrast_text": true,
            "audio_descriptions": ["Visual description for accessibility"]
        }}
    }}
}}

Respond with valid JSON only:"""

# Error messages
ERROR_NO_API_KEY = "No OpenRouter API key provided. Set it with --openrouter-key, in a .env file, or as OPENROUTER_API_KEY environment variable."
ERROR_INVALID_MODEL = "Invalid model specified. Available models: {models}"
ERROR_INVALID_STYLE = "Invalid style specified. Available styles: engaging, educational, viral, professional"
ERROR_INVALID_VISUAL_ANIMATION = "Invalid visual animation type. Available types: {types}"
ERROR_INVALID_VISUAL_POSITION = "Invalid visual position. Available positions: {positions}"
ERROR_INVALID_VISUAL_STYLE = "Invalid visual style. Available styles: {styles}"
ERROR_INVALID_TRANSITION_TYPE = "Invalid transition type. Available types: {types}"

# Validation functions
def validate_visual_animation(animation_type: str) -> bool:
    """Validate visual animation type."""
    return animation_type in VISUAL_ANIMATION_TYPES

def validate_visual_position(position: str) -> bool:
    """Validate visual position."""
    return position in VISUAL_POSITIONS

def validate_visual_style(style: str) -> bool:
    """Validate visual style."""
    return style in VISUAL_STYLES

def validate_transition_type(transition_type: str) -> bool:
    """Validate transition type."""
    return transition_type in TRANSITION_TYPES

def get_visual_curation_settings() -> dict:
    """Get all visual curation settings as a dictionary."""
    return {
        "enable_visual_curation": ENABLE_VISUAL_CURATION,
        "max_visual_elements_per_section": MAX_VISUAL_ELEMENTS_PER_SECTION,
        "default_visual_element_duration": DEFAULT_VISUAL_ELEMENT_DURATION,
        "enable_timeline_export": ENABLE_TIMELINE_EXPORT,
        "enable_automatic_transitions": ENABLE_AUTOMATIC_TRANSITIONS,
        "default_transition_duration": DEFAULT_TRANSITION_DURATION,
        "max_replies_for_visual_curation": MAX_REPLIES_FOR_VISUAL_CURATION,
        "min_reply_engagement_threshold": MIN_REPLY_ENGAGEMENT_THRESHOLD,
        "prioritize_verified_authors": PRIORITIZE_VERIFIED_AUTHORS
    }

# Available script styles with descriptions
SCRIPT_STYLES = {
    "engaging": "Conversational and relatable tone that connects with viewers",
    "educational": "Informative and clear explanations focused on learning",
    "viral": "High-energy, trend-focused content designed for maximum reach",
    "professional": "Polished and authoritative tone for business/tech content"
}
