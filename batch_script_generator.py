"""
Batch script generator for processing multiple downloaded threads.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import click

# Import local modules
from script_generator import ScriptGenerator
import config_openrouter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('x-thread-dl.batch_script_generator')

class BatchScriptGenerator:
    """
    Processes multiple downloaded threads and generates TikTok scripts for each.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = config_openrouter.DEFAULT_MODEL):
        """
        Initialize the batch script generator.
        
        Args:
            api_key (Optional[str]): OpenRouter API key
            model (str): LLM model to use for generation
        """
        self.script_generator = ScriptGenerator(api_key, model)
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
    
    def find_thread_directories(self, base_output_dir: Path) -> List[Path]:
        """
        Find all thread directories in the output directory.
        
        Args:
            base_output_dir (Path): Base output directory
            
        Returns:
            List[Path]: List of thread directory paths
        """
        thread_dirs = []
        
        try:
            if not base_output_dir.exists():
                logger.error(f"Output directory does not exist: {base_output_dir}")
                return thread_dirs
            
            # Look for user directories
            for user_dir in base_output_dir.iterdir():
                if user_dir.is_dir():
                    # Look for thread directories within user directories
                    for thread_dir in user_dir.iterdir():
                        if thread_dir.is_dir():
                            # Check if it contains thread_text.json
                            thread_file = thread_dir / "thread_text.json"
                            if thread_file.exists():
                                thread_dirs.append(thread_dir)
                                logger.debug(f"Found thread directory: {thread_dir}")
            
            logger.info(f"Found {len(thread_dirs)} thread directories")
            return thread_dirs
            
        except Exception as e:
            logger.error(f"Error finding thread directories: {str(e)}", exc_info=True)
            return thread_dirs
    
    def should_process_thread(self, thread_dir: Path, force_regenerate: bool = False) -> bool:
        """
        Check if a thread should be processed (script doesn't exist or force regenerate).
        
        Args:
            thread_dir (Path): Thread directory path
            force_regenerate (bool): Force regeneration even if script exists
            
        Returns:
            bool: True if thread should be processed
        """
        script_file = thread_dir / "tiktok_script.json"
        
        if force_regenerate:
            return True
        
        if not script_file.exists():
            return True
        
        logger.debug(f"Script already exists for {thread_dir.name}, skipping")
        return False
    
    async def process_single_thread(
        self,
        thread_dir: Path,
        style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
        target_duration: int = config_openrouter.DEFAULT_TARGET_DURATION,
        include_replies: bool = True,
        force_regenerate: bool = False
    ) -> bool:
        """
        Process a single thread directory.
        
        Args:
            thread_dir (Path): Thread directory path
            style (str): Script style
            target_duration (int): Target duration in seconds
            include_replies (bool): Whether to include replies
            force_regenerate (bool): Force regeneration even if script exists
            
        Returns:
            bool: True if processed successfully
        """
        try:
            self.processed_count += 1
            
            if not self.should_process_thread(thread_dir, force_regenerate):
                logger.info(f"Skipping {thread_dir.name} (script already exists)")
                return True
            
            logger.info(f"Processing thread {self.processed_count}: {thread_dir.name}")
            
            # Generate script
            script_data = await self.script_generator.process_thread_directory(
                thread_dir, style, target_duration, include_replies
            )
            
            if script_data:
                # Save script
                script_file = thread_dir / "tiktok_script.json"
                if self.script_generator.save_script(script_data, script_file):
                    self.success_count += 1
                    logger.info(f"✅ Successfully generated script for {thread_dir.name}")
                    return True
                else:
                    self.error_count += 1
                    logger.error(f"❌ Failed to save script for {thread_dir.name}")
                    return False
            else:
                self.error_count += 1
                logger.error(f"❌ Failed to generate script for {thread_dir.name}")
                return False
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Error processing {thread_dir.name}: {str(e)}", exc_info=True)
            return False
    
    async def process_all_threads(
        self,
        base_output_dir: Path,
        style: str = config_openrouter.DEFAULT_SCRIPT_STYLE,
        target_duration: int = config_openrouter.DEFAULT_TARGET_DURATION,
        include_replies: bool = True,
        force_regenerate: bool = False,
        max_concurrent: int = 3
    ) -> Dict[str, int]:
        """
        Process all threads in the output directory.
        
        Args:
            base_output_dir (Path): Base output directory
            style (str): Script style
            target_duration (int): Target duration in seconds
            include_replies (bool): Whether to include replies
            force_regenerate (bool): Force regeneration even if scripts exist
            max_concurrent (int): Maximum concurrent processing
            
        Returns:
            Dict[str, int]: Processing statistics
        """
        try:
            logger.info(f"Starting batch processing in: {base_output_dir}")
            
            # Find all thread directories
            thread_dirs = self.find_thread_directories(base_output_dir)
            
            if not thread_dirs:
                logger.warning("No thread directories found")
                return {"processed": 0, "success": 0, "errors": 0}
            
            # Reset counters
            self.processed_count = 0
            self.success_count = 0
            self.error_count = 0
            
            # Create semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(thread_dir):
                async with semaphore:
                    return await self.process_single_thread(
                        thread_dir, style, target_duration, include_replies, force_regenerate
                    )
            
            # Process all threads concurrently (with limit)
            tasks = [process_with_semaphore(thread_dir) for thread_dir in thread_dirs]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log final statistics
            logger.info(f"Batch processing complete!")
            logger.info(f"📊 Statistics:")
            logger.info(f"   Total processed: {self.processed_count}")
            logger.info(f"   ✅ Successful: {self.success_count}")
            logger.info(f"   ❌ Errors: {self.error_count}")
            
            return {
                "processed": self.processed_count,
                "success": self.success_count,
                "errors": self.error_count
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
            return {"processed": 0, "success": 0, "errors": 1}

# CLI interface for batch processing
@click.command()
@click.argument('output_dir', type=click.Path(exists=True, path_type=Path))
@click.option('--openrouter-key', '-k', default=None,
              help='OpenRouter API key (can also be set as OPENROUTER_API_KEY environment variable)')
@click.option('--model', '-m', default=config_openrouter.DEFAULT_MODEL,
              type=click.Choice(config_openrouter.AVAILABLE_MODELS),
              help=f'LLM model to use (default: {config_openrouter.DEFAULT_MODEL})')
@click.option('--style', '-s', default=config_openrouter.DEFAULT_SCRIPT_STYLE,
              type=click.Choice(list(config_openrouter.SCRIPT_STYLES.keys())),
              help=f'Script style (default: {config_openrouter.DEFAULT_SCRIPT_STYLE})')
@click.option('--duration', '-d', default=config_openrouter.DEFAULT_TARGET_DURATION,
              type=int,
              help=f'Target duration in seconds (default: {config_openrouter.DEFAULT_TARGET_DURATION})')
@click.option('--no-replies', is_flag=True,
              help='Exclude replies from script generation')
@click.option('--force', '-f', is_flag=True,
              help='Force regeneration even if scripts already exist')
@click.option('--max-concurrent', default=3, type=int,
              help='Maximum concurrent processing (default: 3)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose (DEBUG level) output')
def main(output_dir: Path, openrouter_key: Optional[str], model: str, style: str, 
         duration: int, no_replies: bool, force: bool, max_concurrent: int, verbose: bool):
    """
    Generate TikTok scripts for all downloaded threads in OUTPUT_DIR.
    
    OUTPUT_DIR: Directory containing downloaded thread data (e.g., 'output')
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    async def run_batch_processing():
        try:
            # Initialize batch generator
            batch_generator = BatchScriptGenerator(openrouter_key, model)
            
            # Process all threads
            stats = await batch_generator.process_all_threads(
                output_dir,
                style=style,
                target_duration=duration,
                include_replies=not no_replies,
                force_regenerate=force,
                max_concurrent=max_concurrent
            )
            
            # Print final summary
            click.echo(f"\n🎬 Batch Script Generation Complete!")
            click.echo(f"📊 Final Statistics:")
            click.echo(f"   Total processed: {stats['processed']}")
            click.echo(f"   ✅ Successful: {stats['success']}")
            click.echo(f"   ❌ Errors: {stats['errors']}")
            
            if stats['errors'] > 0:
                click.echo(f"\n⚠️  Some scripts failed to generate. Check the logs for details.")
                return 1
            else:
                click.echo(f"\n🎉 All scripts generated successfully!")
                return 0
                
        except Exception as e:
            logger.error(f"Fatal error in batch processing: {str(e)}", exc_info=True)
            click.echo(f"❌ Fatal error: {str(e)}")
            return 1
    
    # Run the async function
    exit_code = asyncio.run(run_batch_processing())
    exit(exit_code)

if __name__ == '__main__':
    main()
