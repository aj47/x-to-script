# x-thread-dl

A Python CLI tool to download media from X.com (Twitter) threads and generate TikTok video scripts using AI.

## Overview

Given a tweet URL, this tool:
1. Downloads the original tweet and up to 50 replies
2. Extracts and saves text data and videos in a structured format
3. **NEW**: Generates TikTok video scripts using LLM analysis via OpenRouter API
4. Supports batch processing of multiple threads

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
- `--script-model`, `-m`: LLM model to use (default: claude-3.5-sonnet)
- `--no-replies-in-script`: Exclude replies from script generation

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

## How It Works

### Thread Downloading
1. **Fetching Tweets**: Uses Apify API to fetch the original tweet and replies
2. **Data Parsing**: Extracts user info, thread ID, text content, and video URLs
3. **Structured Storage**: Saves content in organized directory structure
4. **Media Download**: Downloads videos using yt-dlp with quality selection

### Script Generation
1. **Content Analysis**: Extracts and formats thread text and replies
2. **LLM Processing**: Sends content to OpenRouter API with style-specific prompts
3. **Script Structuring**: Parses AI response into Hook/Intro/Explainer format
4. **Metadata Enhancement**: Adds hashtags, key points, and visual suggestions

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

## Integration as Python Module

```python
import asyncio
from pathlib import Path
from script_generator import ScriptGenerator

async def generate_script_example():
    # Initialize generator
    generator = ScriptGenerator(
        api_key="your_openrouter_key",
        model="anthropic/claude-3.5-sonnet"
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

1. **Missing API Keys**: Ensure both APIFY_API_TOKEN and OPENROUTER_API_KEY are set
2. **Import Errors**: Install litellm with `pip install litellm`
3. **Rate Limits**: Use `--max-concurrent` to limit concurrent requests
4. **Model Errors**: Check available models at [openrouter.ai](https://openrouter.ai)

### Debug Mode
```bash
python main.py <url> --verbose --generate-script
```

## License

MIT
