# x-thread-dl

A Python CLI tool to download videos from X.com (Twitter) threads.

## Overview

Given a tweet URL, this tool:
1. Downloads the original tweet and up to 50 replies
2. Identifies if the replies form a thread (consecutive replies from the original author)
3. Extracts and saves text data from the tweets
4. Downloads videos from the thread
5. **NEW**: Generates TikTok video scripts from scraped thread content using OpenRouter AI

- Videos are saved with the naming convention `author_tweetID.mp4`
- Text data is saved as JSON files with the naming convention `author_tweetID_thread.json`
- **NEW**: TikTok scripts are generated as JSON files with hooks, intros, and explainers

## Requirements

- Python 3.7+
- Apify API token (sign up at [apify.com](https://apify.com))
- **NEW**: OpenRouter API key for TikTok script generation (sign up at [openrouter.ai](https://openrouter.ai))

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

4. Set up your Apify API token (required):
   - Create a `.env` file in the project directory with:
     ```
     APIFY_API_TOKEN=your_apify_token_here
     ```
   - Or set it as an environment variable:
     ```
     export APIFY_API_TOKEN=your_apify_token_here  # On Windows: set APIFY_API_TOKEN=your_apify_token_here
     ```
   - Or pass it as a command-line argument (see Usage below)

5. **NEW**: Set up your OpenRouter API key (for TikTok script generation):
   - Add to your `.env` file:
     ```
     OPENROUTER_API_KEY=your_openrouter_key_here
     ```
   - Or set as environment variable:
     ```
     export OPENROUTER_API_KEY=your_openrouter_key_here
     ```

## Usage

**Basic usage (downloads thread data AND generates TikTok script automatically):**
```
python main.py https://twitter.com/username/status/123456789
```

**With options:**
```
python main.py https://twitter.com/username/status/123456789 --reply-limit 100 --output-dir ./my_videos --model gpt-4o
```

**Skip script generation (original behavior):**
```
python main.py https://twitter.com/username/status/123456789 --skip-script
```

### Options

#### Download Options
- `--reply-limit`, `-r`: Maximum number of replies to fetch (default: 50)
- `--output-dir`, `-o`: Directory to save downloaded videos (default: ./downloaded_videos)
- `--apify-token`, `-t`: Apify API token (can also be set as APIFY_API_TOKEN environment variable or in a .env file)
- `--verbose`, `-v`: Enable verbose output
- `--list-formats`: List available video formats before downloading

#### TikTok Script Generation Options (NEW)
- `--skip-script`: Skip automatic TikTok script generation
- `--openrouter-key`, `-k`: OpenRouter API key for script generation
- `--model`, `-m`: OpenRouter model to use (default: claude-3.5-sonnet)

#### Available Models

- `claude-3.5-sonnet` (default) - Best for creative content
- `gpt-4o` - OpenAI's latest model
- `gpt-4o-mini` - Faster, cost-effective option
- `llama-3.1-70b` - Open source alternative
- `gemini-pro` - Google's model

### Additional Tools

**Batch Script Generation:**
```
python batch_script_generator.py [directory_path]
```

**Demo Script:**
```
python example_script_generation.py
```

**Manual Script Generation (if needed):**
```
python main.py generate-script <path_to_thread_json>
```

## How It Works

### Thread Download Process

1. **Fetching Tweets**: Uses the Apify API to fetch the original tweet and its replies.
2. **Thread Identification**: Identifies if the replies form a thread by checking if consecutive replies are from the original author.
3. **Text Extraction**: Extracts text content and metadata from the tweets in the thread.
4. **Text Storage**: Saves the extracted text data as JSON files in the `tweet_text` subdirectory.
5. **Video Extraction**: Extracts video URLs from the tweets in the thread.
6. **Video Download**: Downloads the videos using yt-dlp and saves them with the naming convention `author_tweetID.mp4`.

### TikTok Script Generation Process (NEW)

1. **Content Analysis**: Reads and processes the scraped thread JSON data
2. **AI Processing**: Sends the thread content to OpenRouter API with specialized prompts
3. **Script Structure**: Generates structured scripts with three main sections:
   - **Hook** (0-15s): Attention-grabbing opening
   - **Intro** (15-35s): Topic introduction and context
   - **Explainer** (35-60s): Key insights and details
4. **Metadata Generation**: Creates hashtags, topics, and audience targeting suggestions
5. **Output**: Saves the complete script as a JSON file with visual cues and timing

## Text Data Format

The text data is saved as a JSON file containing an array of tweet objects. Each tweet object includes:

- `tweet_id`: The ID of the tweet
- `author`: The screen name of the tweet author
- `text`: The text content of the tweet
- `timestamp`: The creation timestamp of the tweet
- `urls`: Array of URLs included in the tweet
- `hashtags`: Array of hashtags used in the tweet
- `mentions`: Array of user mentions in the tweet
- `is_reply`: Boolean indicating if the tweet is a reply
- `reply_to`: The screen name of the user being replied to (if applicable)
- `reply_to_id`: The ID of the tweet being replied to (if applicable)

## License

MIT
