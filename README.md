# x-thread-dl

A Python CLI tool to download videos from X.com (Twitter) threads.

## Overview

Given a tweet URL, this tool:
1. Downloads the original tweet and up to 50 replies
2. Identifies if the replies form a thread (consecutive replies from the original author)
3. Extracts and saves text data from the tweets
4. Downloads videos from the thread

- Videos are saved with the naming convention `author_tweetID.mp4`
- Text data is saved as JSON files with the naming convention `author_tweetID_thread.json`

## Requirements

- Python 3.7+
- Apify API token (sign up at [apify.com](https://apify.com))

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

## Usage

Basic usage:
```
python main.py https://twitter.com/username/status/123456789
```

With options:
```
python main.py https://twitter.com/username/status/123456789 --reply-limit 100 --output-dir ./my_videos
```

### Options

- `--reply-limit`, `-r`: Maximum number of replies to fetch (default: 50)
- `--output-dir`, `-o`: Directory to save downloaded videos (default: ./downloaded_videos)
- `--apify-token`, `-t`: Apify API token (can also be set as APIFY_API_TOKEN environment variable or in a .env file)
- `--verbose`, `-v`: Enable verbose output

## How It Works

1. **Fetching Tweets**: Uses the Apify API to fetch the original tweet and its replies.
2. **Thread Identification**: Identifies if the replies form a thread by checking if consecutive replies are from the original author.
3. **Text Extraction**: Extracts text content and metadata from the tweets in the thread.
4. **Text Storage**: Saves the extracted text data as JSON files in the `tweet_text` subdirectory.
5. **Video Extraction**: Extracts video URLs from the tweets in the thread.
6. **Video Download**: Downloads the videos using yt-dlp and saves them with the naming convention `author_tweetID.mp4`.

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
