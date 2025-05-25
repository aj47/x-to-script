#!/usr/bin/env python3
"""
Example script demonstrating TikTok script generation from scraped Twitter threads.

This script shows how to:
1. Load existing thread JSON data
2. Generate TikTok scripts using OpenRouter API
3. Save and display the results

Usage:
    python example_script_generation.py
"""

import os
import asyncio
import json
from pathlib import Path
from script_generator import ScriptGenerator
import config_openrouter

async def main():
    """Main example function."""
    
    # Check if OpenRouter API key is available
    if not config_openrouter.OPENROUTER_API_KEY:
        print("❌ OpenRouter API key not found!")
        print("Please set OPENROUTER_API_KEY environment variable or add it to .env file")
        print("Get your API key from: https://openrouter.ai/")
        return
    
    # Find existing thread JSON files
    json_files = []
    
    # Check common locations for thread data
    search_paths = [
        "downloaded_videos/tweet_text",
        "output",
        "test_output/tweet_text"
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith('.json') and ('thread' in file or 'tweet' in file):
                        json_files.append(os.path.join(root, file))
    
    if not json_files:
        print("❌ No thread JSON files found!")
        print("Please run the main script first to download some thread data:")
        print("python main.py download <tweet_url>")
        return
    
    print(f"📁 Found {len(json_files)} thread JSON files:")
    for i, file_path in enumerate(json_files[:5]):  # Show first 5
        print(f"  {i+1}. {file_path}")
    
    if len(json_files) > 5:
        print(f"  ... and {len(json_files) - 5} more")
    
    # Use the first file for demonstration
    demo_file = json_files[0]
    print(f"\n🎬 Generating TikTok script for: {demo_file}")
    
    try:
        # Initialize script generator
        generator = ScriptGenerator()
        
        # Process the thread file
        output_path = await generator.process_thread_file(demo_file)
        
        if output_path:
            print(f"✅ Script generated successfully!")
            print(f"📄 Saved to: {output_path}")
            
            # Display the generated script
            with open(output_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            print("\n" + "="*60)
            print("🎥 GENERATED TIKTOK SCRIPT")
            print("="*60)
            
            # Display hook
            hook = script_data.get('hook', {})
            print(f"\n🪝 HOOK ({hook.get('duration_seconds', 0)}s):")
            print(f"   {hook.get('text', 'N/A')}")
            if hook.get('visual_cues'):
                print(f"   💡 Visual: {hook.get('visual_cues')}")
            
            # Display intro
            intro = script_data.get('intro', {})
            print(f"\n👋 INTRO ({intro.get('duration_seconds', 0)}s):")
            print(f"   {intro.get('text', 'N/A')}")
            if intro.get('visual_cues'):
                print(f"   💡 Visual: {intro.get('visual_cues')}")
            
            # Display explainer
            explainer = script_data.get('explainer', {})
            print(f"\n📚 EXPLAINER ({explainer.get('duration_seconds', 0)}s):")
            print(f"   {explainer.get('text', 'N/A')}")
            if explainer.get('visual_cues'):
                print(f"   💡 Visual: {explainer.get('visual_cues')}")
            
            # Display metadata
            metadata = script_data.get('metadata', {})
            print(f"\n📊 METADATA:")
            print(f"   Total Duration: {metadata.get('total_duration', 0)}s")
            print(f"   Key Topics: {', '.join(metadata.get('key_topics', []))}")
            print(f"   Hashtags: {' '.join(metadata.get('suggested_hashtags', []))}")
            print(f"   Engagement Potential: {metadata.get('engagement_potential', 'N/A')}")
            print(f"   Target Audience: {metadata.get('target_audience', 'N/A')}")
            
            print("\n" + "="*60)
            
        else:
            print("❌ Failed to generate script. Check the logs for details.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
