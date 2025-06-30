# x-thread-dl

A Python CLI tool to download media from X.com (Twitter) threads and generate TikTok video scripts using AI.

## Overview

Given a tweet URL, this tool:
1. Downloads the original tweet and up to 50 replies
2. Extracts and saves text data and videos in a structured format
3. **NEW**: Generates TikTok video scripts using LLM analysis via OpenRouter API
4. **NEW**: Analyzes downloaded videos using Gemini API for enhanced script generation
5. Supports batch processing of multiple threads

### Key Features
- **Thread Downloading**: Download complete Twitter/X threads with replies
- **Media Extraction**: Save videos and text content in organized directories
- **🎬 TikTok Script Generation**: AI-powered script creation with Hook, Intro, and Explainer sections
- **Multiple Script Styles**: Engaging, Educational, Viral, and Professional styles
- **Batch Processing**: Generate scripts for all downloaded threads at once
- **Flexible Integration**: Use as CLI tool or import as Python modules

## Requirements

- Python 3.8+
- Apify API token (sign up at [apify.com](https://apify.com)) - for downloading threads
- OpenRouter API key (sign up at [openrouter.ai](https://openrouter.ai)) - for script generation
- **Optional**: Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey)) - for video analysis

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/x-thread-dl.git
   cd x-thread-dl
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your API tokens:
   - Create a `.env` file in the project directory with:
     ```
     APIFY_API_TOKEN=your_apify_token_here
     OPENROUTER_API_KEY=your_openrouter_key_here
     GEMINI_API_KEY=your_gemini_key_here  # Optional, for video analysis
     ```
   - Or set them as environment variables:
     ```
     export APIFY_API_TOKEN=your_apify_token_here
     export OPENROUTER_API_KEY=your_openrouter_key_here
     ```
   - Or pass them as command-line arguments (see Usage below)

## Usage

### Basic Thread Downloading
```bash
python main.py https://x.com/username/status/123456789
```

### Download + Generate TikTok Script (Recommended)
```bash
python main.py https://x.com/username/status/123456789 --generate-script
```

### Advanced Usage Examples
```bash
# Download with custom script style
python main.py https://x.com/user/status/123 -g --script-style viral

# Generate 45-second professional script
python main.py https://x.com/user/status/123 -g -s professional -d 45

# Download only, no script generation
python main.py https://x.com/user/status/123 --reply-limit 100

# Batch generate scripts for existing downloads
python batch_script_generator.py output/ --style engaging
```

### CLI Options

#### Core Options
- `--reply-limit`, `-r`: Maximum number of replies to fetch (default: 50)
- `--output-dir`, `-o`: Directory to save content (default: ./output)
- `--apify-token`, `-t`: Apify API token
- `--verbose`, `-v`: Enable verbose output

#### Script Generation Options
- `--generate-script`, `-g`: Generate TikTok script after downloading
- `--openrouter-key`, `-k`: OpenRouter API key for script generation
- `--script-style`, `-s`: Script style (engaging, educational, viral, professional)
- `--script-duration`, `-d`: Target duration in seconds (default: 60)
- `--script-model`, `-m`: LLM model to use (default: deepseek/deepseek-r1-0528:free)
- `--no-replies-in-script`: Exclude replies from script generation

#### Video Analysis Options (NEW!)
- `--enable-video-analysis`: Enable video analysis using Gemini API
- `--gemini-key`: Gemini API key for video analysis
- `--video-analysis-model`: Gemini model to use (default: gemini-1.5-pro)

## 🎬 TikTok Script Generation

The tool now includes AI-powered TikTok script generation using OpenRouter API and liteLLM:

### Script Structure
Each generated script includes three sections:
- **Hook** (10-15 seconds): Attention-grabbing opening
- **Intro** (10-15 seconds): Brief context and setup
- **Explainer** (30-40 seconds): Main content breakdown

### Available Styles
- **Engaging**: Conversational and relatable tone
- **Educational**: Informative and clear explanations
- **Viral**: High-energy, trend-focused content
- **Professional**: Polished and authoritative tone

### Supported Models
- **DeepSeek R1 (default, free)** - Fast and capable reasoning model
- Anthropic Claude 3.5 Sonnet
- Anthropic Claude 3 Haiku
- OpenAI GPT-4o / GPT-4o Mini
- Meta Llama 3.1 8B Instruct
- Google Gemini Pro 1.5
- Qwen 2.5 72B Instruct (free)
- Microsoft Phi-3 Medium (free)

### Script Output Format
```json
{
  "hook": {
    "text": "Hook content here",
    "duration_seconds": 15,
    "visual_suggestions": ["suggestion 1", "suggestion 2"]
  },
  "intro": {
    "text": "Intro content here",
    "duration_seconds": 15,
    "visual_suggestions": ["suggestion 1", "suggestion 2"]
  },
  "explainer": {
    "text": "Main explainer content",
    "duration_seconds": 30,
    "visual_suggestions": ["suggestion 1", "suggestion 2"]
  },
  "metadata": {
    "total_duration": 60,
    "style": "engaging",
    "key_points": ["point 1", "point 2"],
    "hashtags": ["#hashtag1", "#hashtag2"]
  }
}
```

## 🆕 Enhanced Visual Content Curation

The latest version includes **advanced visual content curation** that transforms TikTok script generation into a comprehensive video production guide:

### Key Enhancements

#### 🎯 Visual Content Selection
- **Smart Tweet Selection**: AI identifies which specific tweets from the thread should be displayed visually
- **Reply Highlighting**: Automatically selects the most engaging and relevant reply tweets to feature
- **Media Integration**: Includes embedded images and videos from tweets in the visual timeline
- **Author Prioritization**: Considers follower count and verification status when selecting content

#### ⏱️ Timestamp Integration
- **Precise Timing**: Each visual element has exact timestamp specifications (down to the second)
- **Duration Control**: Specifies how long each visual element should remain on screen
- **Narration Sync**: Maps visual content to specific moments in the script narration
- **Transition Timing**: Includes smooth transitions between different visual elements

#### 🎨 Presentation Instructions
- **Animation Types**: fade_in, slide_up, zoom_in, typewriter, highlight effects
- **Positioning**: center, top, bottom, left, right, overlay placements
- **Visual Styles**: full_tweet, text_only, quote_style, highlighted_text, profile_focus
- **Emphasis Effects**: normal, bold, glow, shake, pulse for important content

### Enhanced Script Format

The new format includes a comprehensive `visual_timeline` section:

```json
{
  "visual_timeline": {
    "total_duration": 60,
    "timeline_events": [
      {
        "timestamp": 0,
        "duration": 5,
        "visual_type": "main_tweet",
        "content": "Display original tweet",
        "tweet_id": "1928480376386703849",
        "presentation_details": {
          "animation_in": "fade_in",
          "position": "center",
          "size": "large"
        },
        "sync_with_narration": {
          "narration_text": "Specific part of script this syncs with",
          "emphasis_words": ["key", "words"],
          "timing_cue": "during_word"
        }
      }
    ],
    "tweet_references": {
      "1928480376386703849": {
        "usage_count": 2,
        "display_timestamps": [0, 25],
        "display_style": "full_tweet",
        "highlight_text": ["important phrase"],
        "author_focus": true
      }
    },
    "visual_transitions": [
      {
        "from_timestamp": 14,
        "to_timestamp": 16,
        "transition_type": "fade",
        "duration": 1,
        "easing": "ease_in_out"
      }
    ]
  }
}
```

### Production Benefits
- **Video Editing Ready**: Direct import into editing software with precise timing
- **Consistent Branding**: Standardized visual presentation across all scripts
- **Accessibility Support**: Built-in caption and high-contrast text recommendations
- **Quality Control**: Production notes and software recommendations included

## How It Works

### Thread Downloading
1. **Fetching Tweets**: Uses Apify API to fetch the original tweet and replies
2. **Data Parsing**: Extracts user info, thread ID, text content, and video URLs
3. **Structured Storage**: Saves content in organized directory structure
4. **Media Download**: Downloads videos using yt-dlp with quality selection

### Script Generation
1. **Content Analysis**: Extracts and formats thread text and replies
2. **Video Analysis** (Optional): Uses Gemini API to analyze downloaded videos for visual context
3. **LLM Processing**: Sends content to OpenRouter API with style-specific prompts and video insights
4. **Script Structuring**: Parses AI response into Hook/Intro/Explainer format
5. **Metadata Enhancement**: Adds hashtags, key points, and visual suggestions

## Directory Structure

Downloaded content is organized as follows:
```
output/
├── {username}/
│   └── {thread_id}/
│       ├── thread_text.json          # Main thread content
│       ├── tiktok_script.json         # Generated TikTok script
│       ├── videos/
│       │   └── {thread_id}.mp4        # Thread video
│       └── replies/
│           └── {reply_id}/
│               ├── reply_text.json    # Reply content
│               └── videos/
│                   └── {reply_id}.mp4 # Reply video
```

## Batch Processing

Generate scripts for all downloaded threads:

```bash
# Process all threads with default settings
python batch_script_generator.py output/

# Custom batch processing
python batch_script_generator.py output/ \
  --style viral \
  --duration 45 \
  --model "anthropic/claude-3-haiku" \
  --max-concurrent 5 \
  --force
```

### Batch Options
- `--style`, `-s`: Script style for all threads
- `--duration`, `-d`: Target duration for all scripts
- `--model`, `-m`: LLM model to use
- `--no-replies`: Exclude replies from all scripts
- `--force`, `-f`: Regenerate existing scripts
- `--max-concurrent`: Number of concurrent processing threads

## 📹 Video Analysis (NEW!)

The tool now includes advanced video analysis using Google's Gemini API to enhance TikTok script generation:

### What Video Analysis Provides
- **Scene Description**: Detailed analysis of visual content and key moments
- **Text Extraction**: Identifies any text, captions, or graphics visible in videos
- **Visual Elements**: Detects objects, people, settings, and demonstrations
- **Mood Analysis**: Analyzes emotional tone and overall atmosphere
- **Action Recognition**: Describes significant actions, gestures, or movements
- **Script Integration**: Provides specific suggestions for incorporating visual elements

### Usage with Video Analysis
```bash
# Enable video analysis for enhanced script generation
python main.py "https://twitter.com/username/status/123456789" \
  --generate-script \
  --enable-video-analysis \
  --gemini-key your_gemini_api_key
```

### Video Analysis Models
- **gemini-1.5-pro**: Best for complex video analysis (default)
- **gemini-1.5-flash**: Faster analysis for simple content
- **gemini-1.0-pro-vision**: Legacy model with vision capabilities

### Enhanced Script Output
When video analysis is enabled, scripts include:
- Visual context from analyzed videos
- Scene-specific suggestions for hooks and explanations
- Integration recommendations for visual elements
- Enhanced metadata with video insights

## Integration as Python Module

```python
import asyncio
from pathlib import Path
from script_generator import ScriptGenerator

async def generate_script_example():
    # Initialize generator with video analysis
    generator = ScriptGenerator(
        api_key="your_openrouter_key",
        model="deepseek/deepseek-r1-0528:free",
        enable_video_analysis=True,
        gemini_api_key="your_gemini_key"
    )

    # Generate script for a thread directory
    thread_dir = Path("output/username/thread_id")
    script_data = await generator.process_thread_directory(
        thread_dir,
        style="engaging",
        target_duration=60,
        include_replies=True
    )

    # Save script
    if script_data:
        output_file = thread_dir / "custom_script.json"
        generator.save_script(script_data, output_file)

# Run the example
asyncio.run(generate_script_example())
```

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure APIFY_API_TOKEN and OPENROUTER_API_KEY are set
2. **Video Analysis Issues**: Set GEMINI_API_KEY for video analysis features
3. **Import Errors**: Install required packages with `pip install -r requirements.txt`
4. **Rate Limits**: Use `--max-concurrent` to limit concurrent requests
5. **Model Errors**: Check available models at [openrouter.ai](https://openrouter.ai)
6. **Video File Size**: Gemini API has a 100MB limit for video files

### Debug Mode
```bash
python main.py <url> --verbose --generate-script
```

## License

MIT
