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

# Prompt templates
SYSTEM_PROMPT = """You are an expert TikTok content creator and script writer. Your task is to analyze Twitter/X thread content and create engaging TikTok video scripts.

You specialize in creating viral, attention-grabbing content that follows TikTok best practices:
- Strong hooks that grab attention in the first 3 seconds
- Clear, concise explanations that are easy to follow
- Engaging storytelling that keeps viewers watching
- Proper pacing for short-form video content

Always structure your scripts with three distinct sections:
1. HOOK: An attention-grabbing opening (10-15 seconds)
2. INTRO: Brief context and setup (10-15 seconds) 
3. EXPLAINER: Main content breakdown (30-40 seconds)

Keep the total script length appropriate for TikTok (45-60 seconds when spoken)."""

SCRIPT_GENERATION_PROMPT = """Analyze the following Twitter/X thread content and create a TikTok video script.

Thread Content:
{thread_content}

Requirements:
- Target duration: {target_duration} seconds
- Style: {style}
- Create three sections: Hook, Intro, Explainer
- Make it engaging and suitable for TikTok audience
- Include visual cues or suggestions where appropriate

IMPORTANT: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

JSON Format:
{{
    "hook": {{
        "text": "Hook content here",
        "duration_seconds": 15,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "intro": {{
        "text": "Intro content here",
        "duration_seconds": 15,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "explainer": {{
        "text": "Main explainer content here",
        "duration_seconds": 30,
        "visual_suggestions": ["suggestion 1", "suggestion 2"]
    }},
    "metadata": {{
        "total_duration": {target_duration},
        "style": "{style}",
        "key_points": ["point 1", "point 2", "point 3"],
        "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
    }}
}}

Respond with valid JSON only:"""

# Error messages
ERROR_NO_API_KEY = "No OpenRouter API key provided. Set it with --openrouter-key, in a .env file, or as OPENROUTER_API_KEY environment variable."
ERROR_INVALID_MODEL = "Invalid model specified. Available models: {models}"
ERROR_INVALID_STYLE = "Invalid style specified. Available styles: engaging, educational, viral, professional"

# Available script styles with descriptions
SCRIPT_STYLES = {
    "engaging": "Conversational and relatable tone that connects with viewers",
    "educational": "Informative and clear explanations focused on learning",
    "viral": "High-energy, trend-focused content designed for maximum reach",
    "professional": "Polished and authoritative tone for business/tech content"
}
