#!/usr/bin/env python3
"""
Test script for OpenRouter integration with the new DeepSeek model.
This script tests the API connection and model configuration.
"""

import os
import asyncio
import logging
from typing import Optional

# Import local modules
import config_openrouter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test-openrouter')

# Suppress verbose logging from external libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)

async def test_openrouter_connection():
    """Test basic OpenRouter API connection."""
    logger.info("🧪 Testing OpenRouter API connection...")
    
    try:
        # Check if API key is available
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("⚠️  OPENROUTER_API_KEY not found in environment")
            logger.info("To test with real API:")
            logger.info("1. Get API key from https://openrouter.ai/")
            logger.info("2. Set environment variable: export OPENROUTER_API_KEY=your_key")
            logger.info("3. Run this test again")
            return False
        
        # Import litellm here to avoid import issues if not available
        try:
            from litellm import completion
        except ImportError:
            logger.error("❌ litellm not installed. Run: pip install litellm")
            return False
        
        # Test with a simple prompt
        logger.info(f"Testing with model: {config_openrouter.DEFAULT_MODEL}")
        
        response = await asyncio.to_thread(
            completion,
            model=f"openrouter/{config_openrouter.DEFAULT_MODEL}",
            messages=[
                {"role": "user", "content": "Say 'Hello, this is a test!' and nothing else."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info(f"✅ API connection successful!")
            logger.info(f"Response: {content}")
            return True
        else:
            logger.error("❌ No response received from API")
            return False
            
    except Exception as e:
        logger.error(f"❌ API connection failed: {str(e)}")
        logger.info("Common issues:")
        logger.info("1. Invalid API key")
        logger.info("2. Network connectivity")
        logger.info("3. Model not available")
        logger.info("4. Rate limiting")
        return False

def test_configuration():
    """Test configuration values."""
    logger.info("🧪 Testing configuration...")
    
    try:
        # Test default model
        default_model = config_openrouter.DEFAULT_MODEL
        logger.info(f"Default model: {default_model}")
        
        if default_model not in config_openrouter.AVAILABLE_MODELS:
            logger.error(f"❌ Default model {default_model} not in available models")
            return False
        
        # Test available models
        logger.info(f"Available models: {len(config_openrouter.AVAILABLE_MODELS)}")
        for model in config_openrouter.AVAILABLE_MODELS:
            logger.info(f"  - {model}")
        
        # Test script styles
        logger.info(f"Available styles: {list(config_openrouter.SCRIPT_STYLES.keys())}")
        
        # Test prompts
        if not config_openrouter.SYSTEM_PROMPT:
            logger.error("❌ System prompt is empty")
            return False
        
        if not config_openrouter.SCRIPT_GENERATION_PROMPT:
            logger.error("❌ Script generation prompt is empty")
            return False
        
        logger.info("✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}")
        return False

async def test_script_generation_mock():
    """Test script generation with mock data."""
    logger.info("🧪 Testing script generation (mock)...")
    
    try:
        # Import script generator
        from script_generator import ScriptGenerator
        
        # Check if API key is available
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.info("⚠️  Skipping real API test (no API key)")
            logger.info("Testing configuration only...")
            
            # Test that we can create the generator class
            try:
                # This will fail due to no API key, but we can catch it
                generator = ScriptGenerator()
            except ValueError as e:
                if "No OpenRouter API key" in str(e):
                    logger.info("✅ API key validation working correctly")
                    return True
                else:
                    raise e
        else:
            # Test with real API
            logger.info("🚀 Testing with real API...")
            generator = ScriptGenerator(api_key, config_openrouter.DEFAULT_MODEL)
            
            # Test text extraction
            mock_thread_data = {
                "id_str": "123456789",
                "text": "This is a test thread about AI technology and its impact on society.",
                "user": {
                    "name": "Test User",
                    "screen_name": "testuser"
                }
            }
            
            extracted_text = generator.extract_thread_text(mock_thread_data)
            logger.info(f"✅ Text extraction: {extracted_text[:50]}...")
            
            # Test script generation with a simple prompt
            logger.info("Generating test script...")
            script_data = await generator.generate_script(
                extracted_text,
                style="engaging",
                target_duration=30
            )
            
            if script_data:
                logger.info("✅ Script generation successful!")
                if "hook" in script_data:
                    logger.info(f"Hook: {script_data['hook'].get('text', 'N/A')[:50]}...")
                return True
            else:
                logger.error("❌ Script generation failed")
                return False
        
    except Exception as e:
        logger.error(f"❌ Script generation test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all OpenRouter integration tests."""
    logger.info("🚀 Starting OpenRouter integration tests...")
    logger.info(f"Default model: {config_openrouter.DEFAULT_MODEL}")
    
    tests = [
        ("Configuration", test_configuration),
        ("Script Generation (Mock)", test_script_generation_mock),
        ("OpenRouter API Connection", test_openrouter_connection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info(f"{'='*50}")
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 All tests passed! OpenRouter integration is working.")
        logger.info("\nTo use the script generation:")
        logger.info("1. Set OPENROUTER_API_KEY environment variable")
        logger.info("2. Run: python main.py <tweet_url> --generate-script")
    else:
        logger.error(f"\n💥 {failed} test(s) failed. Check the configuration.")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_all_tests())
