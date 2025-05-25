#!/usr/bin/env python3
"""
Batch TikTok Script Generator

This script processes multiple Twitter thread JSON files and generates
TikTok scripts for all of them in batch mode.

Usage:
    python batch_script_generator.py [directory_path]
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import click

from script_generator import ScriptGenerator
import config_openrouter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('batch_script_generator')

class BatchScriptGenerator:
    """Handles batch processing of multiple thread files."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the batch generator."""
        self.generator = ScriptGenerator(api_key=api_key, model=model)
        self.results = []
    
    def find_thread_files(self, directory: str) -> List[str]:
        """
        Find all thread JSON files in a directory and its subdirectories.
        
        Args:
            directory: Directory to search for JSON files
            
        Returns:
            List of paths to thread JSON files
        """
        json_files = []
        
        if not os.path.exists(directory):
            logger.error(f"Directory not found: {directory}")
            return json_files
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json') and ('thread' in file.lower() or 'tweet' in file.lower()):
                    file_path = os.path.join(root, file)
                    json_files.append(file_path)
        
        logger.info(f"Found {len(json_files)} thread JSON files in {directory}")
        return json_files
    
    async def process_file_with_retry(self, file_path: str, output_dir: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Process a single file with retry logic.
        
        Args:
            file_path: Path to the JSON file
            output_dir: Output directory for scripts
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'file_path': file_path,
            'success': False,
            'output_path': None,
            'error': None,
            'attempts': 0
        }
        
        for attempt in range(max_retries):
            result['attempts'] = attempt + 1
            
            try:
                logger.info(f"Processing {file_path} (attempt {attempt + 1}/{max_retries})")
                
                output_path = await self.generator.process_thread_file(file_path, output_dir)
                
                if output_path:
                    result['success'] = True
                    result['output_path'] = output_path
                    logger.info(f"✅ Successfully processed: {file_path}")
                    break
                else:
                    logger.warning(f"⚠️ Failed to process: {file_path} (attempt {attempt + 1})")
                    
            except Exception as e:
                error_msg = str(e)
                result['error'] = error_msg
                logger.error(f"❌ Error processing {file_path} (attempt {attempt + 1}): {error_msg}")
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        return result
    
    async def process_batch(self, file_paths: List[str], output_dir: str, 
                          concurrent_limit: int = 3) -> List[Dict[str, Any]]:
        """
        Process multiple files concurrently with rate limiting.
        
        Args:
            file_paths: List of JSON file paths to process
            output_dir: Output directory for generated scripts
            concurrent_limit: Maximum number of concurrent requests
            
        Returns:
            List of processing results
        """
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def process_with_semaphore(file_path: str):
            async with semaphore:
                return await self.process_file_with_retry(file_path, output_dir)
        
        logger.info(f"Starting batch processing of {len(file_paths)} files...")
        logger.info(f"Concurrent limit: {concurrent_limit}")
        
        # Process files concurrently
        tasks = [process_with_semaphore(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'file_path': file_paths[i],
                    'success': False,
                    'output_path': None,
                    'error': str(result),
                    'attempts': 1
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a summary report of batch processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            Formatted report string
        """
        total_files = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total_files - successful
        
        report = [
            "="*60,
            "BATCH PROCESSING REPORT",
            "="*60,
            f"Total files processed: {total_files}",
            f"Successful: {successful}",
            f"Failed: {failed}",
            f"Success rate: {(successful/total_files)*100:.1f}%",
            ""
        ]
        
        if successful > 0:
            report.append("✅ SUCCESSFUL GENERATIONS:")
            for result in results:
                if result['success']:
                    report.append(f"  • {Path(result['file_path']).name} → {Path(result['output_path']).name}")
            report.append("")
        
        if failed > 0:
            report.append("❌ FAILED GENERATIONS:")
            for result in results:
                if not result['success']:
                    error = result.get('error', 'Unknown error')
                    report.append(f"  • {Path(result['file_path']).name}: {error}")
        
        return "\n".join(report)

@click.command()
@click.argument('directory', default='.')
@click.option('--output-dir', '-o', default=None,
              help='Output directory for generated scripts')
@click.option('--model', '-m', default=None,
              help='OpenRouter model to use')
@click.option('--concurrent', '-c', default=3, type=int,
              help='Number of concurrent requests (default: 3)')
@click.option('--openrouter-key', '-k', default=None,
              help='OpenRouter API key')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def main(directory: str, output_dir: str, model: str, concurrent: int, 
         openrouter_key: str, verbose: bool):
    """
    Generate TikTok scripts for all thread JSON files in a directory.
    
    DIRECTORY: Directory to search for thread JSON files (default: current directory)
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async def run_batch():
        try:
            # Initialize batch generator
            batch_gen = BatchScriptGenerator(api_key=openrouter_key, model=model)
            
            # Find thread files
            thread_files = batch_gen.find_thread_files(directory)
            
            if not thread_files:
                click.echo(f"❌ No thread JSON files found in: {directory}")
                return
            
            click.echo(f"📁 Found {len(thread_files)} thread files")
            
            # Set output directory
            if not output_dir:
                output_dir = config_openrouter.DEFAULT_SCRIPT_OUTPUT_DIR
            
            # Process files
            results = await batch_gen.process_batch(thread_files, output_dir, concurrent)
            
            # Generate and display report
            report = batch_gen.generate_report(results)
            click.echo(report)
            
            # Save report to file
            report_path = os.path.join(output_dir, 'batch_processing_report.txt')
            os.makedirs(output_dir, exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            click.echo(f"\n📄 Report saved to: {report_path}")
            
        except Exception as e:
            click.echo(f"❌ Error during batch processing: {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    # Run the async function
    asyncio.run(run_batch())

if __name__ == '__main__':
    main()
