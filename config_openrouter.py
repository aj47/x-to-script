"""
Configuration settings for OpenRouter API integration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model for script generation
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

# Alternative models available on OpenRouter
AVAILABLE_MODELS = {
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini", 
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "gemini-pro": "google/gemini-pro",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct"
}

# TikTok Script Generation Settings
SCRIPT_SETTINGS = {
    "max_hook_length": 15,  # seconds
    "max_intro_length": 20,  # seconds  
    "max_explainer_length": 45,  # seconds
    "target_total_length": 60,  # seconds
    "tone": "engaging",  # engaging, educational, entertaining, dramatic
    "style": "conversational"  # conversational, formal, casual, energetic
}

# Prompt templates
TIKTOK_SCRIPT_PROMPT = """
You are an expert TikTok content creator specializing in viral, engaging short-form videos. 

Your task is to analyze the provided Twitter/X thread content and create a compelling TikTok video script.

THREAD CONTENT TO ANALYZE:
{thread_content}

REQUIREMENTS:
1. **HOOK (0-15 seconds)**: Create an attention-grabbing opening that makes viewers want to keep watching
2. **INTRO (15-35 seconds)**: Introduce the main topic/story in an engaging way
3. **EXPLAINER (35-60 seconds)**: Deliver the key insights, facts, or story details

GUIDELINES:
- Keep total script under 60 seconds when spoken
- Use conversational, energetic tone
- Include specific details from the thread
- Make it shareable and engaging
- Use short, punchy sentences
- Include natural pauses and emphasis cues
- Consider visual elements that could accompany the script

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{{
    "hook": {{
        "text": "Your hook text here",
        "duration_seconds": 15,
        "visual_cues": "Suggested visual elements"
    }},
    "intro": {{
        "text": "Your intro text here", 
        "duration_seconds": 20,
        "visual_cues": "Suggested visual elements"
    }},
    "explainer": {{
        "text": "Your explainer text here",
        "duration_seconds": 25,
        "visual_cues": "Suggested visual elements"
    }},
    "metadata": {{
        "total_duration": 60,
        "key_topics": ["topic1", "topic2"],
        "suggested_hashtags": ["#hashtag1", "#hashtag2"],
        "engagement_potential": "high/medium/low",
        "target_audience": "description of target audience"
    }}
}}

Focus on making this content viral-worthy while staying true to the original thread's message.
"""

# Output directory for generated scripts
DEFAULT_SCRIPT_OUTPUT_DIR = "generated_scripts"
