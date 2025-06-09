#!/usr/bin/env python3
"""
Example usage script for the x-thread-dl tool with TikTok script generation.
This script demonstrates how to use the extended functionality.
"""

import asyncio
import logging
from pathlib import Path

# Import local modules
from script_generator import ScriptGenerator
from batch_script_generator import BatchScriptGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('example_usage')

async def example_single_thread_script_generation():
    """
    Example: Generate a script for a single downloaded thread.
    """
    logger.info("🎬 Example: Single Thread Script Generation")
    
    # Path to a downloaded thread (adjust this to match your actual data)
    thread_dir = Path("output/augmentcode/1920162661909868654")
    
    if not thread_dir.exists():
        logger.warning(f"Thread directory not found: {thread_dir}")
        logger.info("Please download a thread first using the main tool, then run this example.")
        return
    
    try:
        # Initialize script generator (you'll need to set OPENROUTER_API_KEY in your .env file)
        script_generator = ScriptGenerator()
        
        # Generate script with different styles
        styles = ["engaging", "educational", "viral", "professional"]
        
        for style in styles:
            logger.info(f"Generating {style} style script...")
            
            script_data = await script_generator.process_thread_directory(
                thread_dir,
                style=style,
                target_duration=60,
                include_replies=True
            )
            
            if script_data:
                # Save with style-specific filename
                output_file = thread_dir / f"tiktok_script_{style}.json"
                script_generator.save_script(script_data, output_file)
                logger.info(f"✅ {style.capitalize()} script saved to: {output_file}")
            else:
                logger.error(f"❌ Failed to generate {style} script")
                
    except Exception as e:
        logger.error(f"Error in single thread example: {str(e)}", exc_info=True)

async def example_batch_script_generation():
    """
    Example: Generate scripts for all downloaded threads.
    """
    logger.info("🎬 Example: Batch Script Generation")
    
    output_dir = Path("output")
    
    if not output_dir.exists():
        logger.warning(f"Output directory not found: {output_dir}")
        logger.info("Please download some threads first using the main tool.")
        return
    
    try:
        # Initialize batch generator
        batch_generator = BatchScriptGenerator()
        
        # Process all threads with engaging style
        stats = await batch_generator.process_all_threads(
            output_dir,
            style="engaging",
            target_duration=60,
            include_replies=True,
            force_regenerate=False,  # Don't regenerate existing scripts
            max_concurrent=2  # Process 2 threads at a time
        )
        
        logger.info(f"📊 Batch processing complete: {stats}")
        
    except Exception as e:
        logger.error(f"Error in batch example: {str(e)}", exc_info=True)

async def example_custom_script_generation():
    """
    Example: Generate a custom script with specific parameters.
    """
    logger.info("🎬 Example: Custom Script Generation")
    
    # Path to a downloaded thread
    thread_dir = Path("output/augmentcode/1920162661909868654")
    
    if not thread_dir.exists():
        logger.warning(f"Thread directory not found: {thread_dir}")
        return
    
    try:
        # Initialize with specific model
        script_generator = ScriptGenerator(model="anthropic/claude-3-haiku")
        
        # Generate a short-form script (30 seconds)
        script_data = await script_generator.process_thread_directory(
            thread_dir,
            style="viral",
            target_duration=30,  # Shorter duration
            include_replies=False  # Only main thread
        )
        
        if script_data:
            output_file = thread_dir / "tiktok_script_custom.json"
            script_generator.save_script(script_data, output_file)
            logger.info(f"✅ Custom script saved to: {output_file}")
            
            # Print script summary
            if "hook" in script_data:
                logger.info(f"📝 Hook: {script_data['hook'].get('text', 'N/A')}")
            if "metadata" in script_data:
                hashtags = script_data['metadata'].get('hashtags', [])
                logger.info(f"🏷️  Suggested hashtags: {', '.join(hashtags)}")
        else:
            logger.error("❌ Failed to generate custom script")
            
    except Exception as e:
        logger.error(f"Error in custom example: {str(e)}", exc_info=True)

def print_usage_instructions():
    """
    Print usage instructions for the tool.
    """
    print("\n" + "="*60)
    print("🎬 X-Thread-DL with TikTok Script Generation")
    print("="*60)
    print()
    print("1. Basic Usage (Download + Generate Script):")
    print("   python main.py <tweet_url> --generate-script")
    print()
    print("2. Download with Custom Script Style:")
    print("   python main.py <tweet_url> -g --script-style viral")
    print()
    print("3. Batch Generate Scripts for Existing Downloads:")
    print("   python batch_script_generator.py output/")
    print()
    print("4. Available Script Styles:")
    print("   - engaging: Conversational and relatable")
    print("   - educational: Informative and clear")
    print("   - viral: High-energy, trend-focused")
    print("   - professional: Polished and authoritative")
    print()
    print("5. Environment Setup:")
    print("   - Set APIFY_API_TOKEN for thread downloading")
    print("   - Set OPENROUTER_API_KEY for script generation")
    print()
    print("6. Example Commands:")
    print("   # Download and generate engaging script")
    print("   python main.py https://x.com/user/status/123 -g")
    print()
    print("   # Generate viral script with 45-second duration")
    print("   python main.py https://x.com/user/status/123 -g -s viral -d 45")
    print()
    print("   # Batch process all downloads with professional style")
    print("   python batch_script_generator.py output/ -s professional")
    print()
    print("="*60)

async def main():
    """
    Run all examples.
    """
    print_usage_instructions()
    
    logger.info("🚀 Starting x-thread-dl script generation examples...")
    
    # Run examples (comment out any you don't want to run)
    await example_single_thread_script_generation()
    await example_batch_script_generation()
    await example_custom_script_generation()
    
    logger.info("✅ All examples completed!")

if __name__ == "__main__":
    asyncio.run(main())
