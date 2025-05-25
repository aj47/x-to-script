# TikTok Script Generation Feature

This feature uses OpenRouter API to process scraped Twitter/X thread content and generate engaging TikTok video scripts with hooks, intros, and explainers.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get OpenRouter API Key

1. Sign up at [OpenRouter.ai](https://openrouter.ai/)
2. Get your API key from the dashboard
3. Set it as an environment variable:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

Or add it to a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

### Command Line Interface

The tool now supports two main commands:

#### 1. Download Thread Data (existing functionality)
```bash
python main.py download <tweet_url>
```

#### 2. Generate TikTok Script (new feature)
```bash
python main.py generate-script <path_to_thread_json>
```

### Examples

1. **Download a thread first:**
```bash
python main.py download https://x.com/username/status/1234567890
```

2. **Generate a TikTok script from the downloaded data:**
```bash
python main.py generate-script downloaded_videos/tweet_text/username_1234567890_thread.json
```

3. **Use a specific model:**
```bash
python main.py generate-script thread.json --model gpt-4o
```

4. **Specify output directory:**
```bash
python main.py generate-script thread.json --output-dir my_scripts
```

### Available Models

The tool supports various models through OpenRouter:

- `claude-3.5-sonnet` (default) - Best for creative content
- `gpt-4o` - OpenAI's latest model
- `gpt-4o-mini` - Faster, cost-effective option
- `llama-3.1-70b` - Open source alternative
- `gemini-pro` - Google's model

### Script Output Format

Generated scripts are saved as JSON files with this structure:

```json
{
  "hook": {
    "text": "Attention-grabbing opening line...",
    "duration_seconds": 15,
    "visual_cues": "Suggested visual elements"
  },
  "intro": {
    "text": "Introduction to the topic...",
    "duration_seconds": 20,
    "visual_cues": "Suggested visual elements"
  },
  "explainer": {
    "text": "Main content and insights...",
    "duration_seconds": 25,
    "visual_cues": "Suggested visual elements"
  },
  "metadata": {
    "total_duration": 60,
    "key_topics": ["topic1", "topic2"],
    "suggested_hashtags": ["#hashtag1", "#hashtag2"],
    "engagement_potential": "high",
    "target_audience": "description of target audience"
  }
}
```

## Configuration

You can customize the script generation by editing `config_openrouter.py`:

### Script Settings
```python
SCRIPT_SETTINGS = {
    "max_hook_length": 15,      # seconds
    "max_intro_length": 20,     # seconds  
    "max_explainer_length": 45, # seconds
    "target_total_length": 60,  # seconds
    "tone": "engaging",         # engaging, educational, entertaining, dramatic
    "style": "conversational"   # conversational, formal, casual, energetic
}
```

### Model Selection
```python
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
```

## Programmatic Usage

You can also use the script generator programmatically:

```python
import asyncio
from script_generator import ScriptGenerator

async def generate_script_example():
    # Initialize generator
    generator = ScriptGenerator()
    
    # Process a thread file
    script_path = await generator.process_thread_file(
        "path/to/thread.json",
        output_dir="my_scripts"
    )
    
    print(f"Script saved to: {script_path}")

# Run the example
asyncio.run(generate_script_example())
```

## Example Demo

Run the included example script to see the feature in action:

```bash
python example_script_generation.py
```

This will:
1. Find existing thread JSON files
2. Generate a TikTok script from one of them
3. Display the formatted output

## Tips for Best Results

1. **Use threads with rich content** - The more detailed and engaging the original thread, the better the generated script
2. **Try different models** - Each model has different strengths for creative content
3. **Customize prompts** - Edit the prompt template in `config_openrouter.py` for your specific needs
4. **Review and edit** - Generated scripts are starting points; always review and customize for your brand voice

## Troubleshooting

### Common Issues

1. **"OpenRouter API key not found"**
   - Make sure you've set the `OPENROUTER_API_KEY` environment variable
   - Check that your `.env` file is in the project root

2. **"No content extracted"**
   - Verify the JSON file contains valid thread data
   - Check that the thread has actual text content

3. **"Failed to parse script JSON"**
   - The AI model may have returned invalid JSON
   - Try a different model or regenerate the script

4. **Rate limiting errors**
   - OpenRouter has rate limits; wait a moment and try again
   - Consider using a different model if one is rate-limited

### Getting Help

- Check the logs with `--verbose` flag for detailed error information
- Ensure your OpenRouter account has sufficient credits
- Verify the input JSON file format matches the expected structure

## Cost Considerations

- Different models have different costs per token
- Claude and GPT models are typically more expensive but higher quality
- Open source models like Llama are more cost-effective
- Check OpenRouter pricing for current rates
