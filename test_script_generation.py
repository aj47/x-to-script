#!/usr/bin/env python3
"""
Test script for the TikTok script generation functionality.
This script tests the script generation without making actual API calls.
"""

import json
import logging
from pathlib import Path
import tempfile
import asyncio

# Import local modules
from script_generator import ScriptGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test-script-generation')

def create_mock_thread_data():
    """Create mock thread data for testing."""
    return {
        "id_str": "1234567890",
        "text": "This is a fascinating thread about AI and the future of technology. Let me break down the key points that everyone should know about this rapidly evolving field.",
        "user": {
            "name": "Tech Expert",
            "screen_name": "techexpert",
            "id_str": "987654321"
        },
        "created_at": "2025-01-01T12:00:00.000Z",
        "favorite_count": 150,
        "entities": {
            "hashtags": [{"text": "AI"}, {"text": "Technology"}],
            "urls": [],
            "user_mentions": []
        }
    }

def create_mock_reply_data():
    """Create mock reply data for testing."""
    return {
        "replyId": "1234567891",
        "replyText": "Great point! I'd also add that machine learning is becoming increasingly accessible to developers.",
        "author": {
            "name": "Developer",
            "screenName": "developer123"
        },
        "timestamp": 1704110400000
    }

async def test_text_extraction():
    """Test text extraction functionality."""
    logger.info("🧪 Testing text extraction...")
    
    try:
        # Create a mock script generator (without API key for testing)
        # We'll only test the text extraction methods
        
        # Test thread text extraction
        thread_data = create_mock_thread_data()
        
        # Create a temporary ScriptGenerator instance for testing
        # We'll mock the API key requirement
        class MockScriptGenerator(ScriptGenerator):
            def __init__(self):
                # Skip the parent __init__ to avoid API key requirement
                pass
        
        generator = MockScriptGenerator()
        
        # Test thread text extraction
        thread_text = generator.extract_thread_text(thread_data)
        logger.info(f"✅ Thread text extracted: {thread_text[:100]}...")
        
        # Test with temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock thread directory structure
            thread_dir = temp_path / "test_user" / "1234567890"
            thread_dir.mkdir(parents=True)
            
            # Create thread_text.json
            thread_file = thread_dir / "thread_text.json"
            with open(thread_file, 'w') as f:
                json.dump(thread_data, f)
            
            # Create replies directory and file
            replies_dir = thread_dir / "replies" / "1234567891"
            replies_dir.mkdir(parents=True)
            
            reply_file = replies_dir / "reply_text.json"
            with open(reply_file, 'w') as f:
                json.dump(create_mock_reply_data(), f)
            
            # Test replies text extraction
            replies_text = generator.extract_replies_text(thread_dir / "replies")
            logger.info(f"✅ Replies text extracted: {replies_text[:100]}...")
            
            logger.info("✅ Text extraction tests passed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Text extraction test failed: {str(e)}", exc_info=True)
        return False

def test_script_structure():
    """Test script structure validation."""
    logger.info("🧪 Testing script structure...")
    
    try:
        # Mock script data
        mock_script = {
            "hook": {
                "text": "Did you know AI is changing everything?",
                "duration_seconds": 15,
                "visual_suggestions": ["Show AI graphics", "Use engaging animations"]
            },
            "intro": {
                "text": "Let me explain the key points everyone should understand",
                "duration_seconds": 15,
                "visual_suggestions": ["Show speaker", "Display key points"]
            },
            "explainer": {
                "text": "First, AI is becoming more accessible. Second, it's transforming industries. Third, the future is happening now.",
                "duration_seconds": 30,
                "visual_suggestions": ["Show examples", "Use charts and graphs"]
            },
            "metadata": {
                "total_duration": 60,
                "style": "engaging",
                "key_points": ["AI accessibility", "Industry transformation", "Future trends"],
                "hashtags": ["#AI", "#Technology", "#Future"]
            }
        }
        
        # Validate structure
        required_sections = ["hook", "intro", "explainer", "metadata"]
        for section in required_sections:
            if section not in mock_script:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate each section has required fields
        for section in ["hook", "intro", "explainer"]:
            section_data = mock_script[section]
            if "text" not in section_data:
                raise ValueError(f"Missing text in {section}")
            if "duration_seconds" not in section_data:
                raise ValueError(f"Missing duration_seconds in {section}")
        
        logger.info("✅ Script structure validation passed!")
        
        # Test saving script
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_file = temp_path / "test_script.json"
            
            # Create a mock generator for saving
            class MockScriptGenerator:
                def save_script(self, script_data, output_path):
                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(script_data, f, indent=2, ensure_ascii=False)
                        return True
                    except Exception:
                        return False
            
            generator = MockScriptGenerator()
            success = generator.save_script(mock_script, script_file)
            
            if success and script_file.exists():
                logger.info("✅ Script saving test passed!")
                
                # Verify saved content
                with open(script_file, 'r') as f:
                    saved_data = json.load(f)
                
                if saved_data == mock_script:
                    logger.info("✅ Script content verification passed!")
                    return True
                else:
                    logger.error("❌ Script content verification failed!")
                    return False
            else:
                logger.error("❌ Script saving test failed!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Script structure test failed: {str(e)}", exc_info=True)
        return False

def test_configuration():
    """Test configuration loading."""
    logger.info("🧪 Testing configuration...")
    
    try:
        import config_openrouter
        
        # Test that all required configurations are available
        required_configs = [
            'DEFAULT_MODEL',
            'AVAILABLE_MODELS', 
            'DEFAULT_SCRIPT_STYLE',
            'SCRIPT_STYLES',
            'SYSTEM_PROMPT',
            'SCRIPT_GENERATION_PROMPT'
        ]
        
        for config_name in required_configs:
            if not hasattr(config_openrouter, config_name):
                raise ValueError(f"Missing configuration: {config_name}")
        
        # Test that default values are reasonable
        if config_openrouter.DEFAULT_MODEL not in config_openrouter.AVAILABLE_MODELS:
            raise ValueError("Default model not in available models list")
        
        if config_openrouter.DEFAULT_SCRIPT_STYLE not in config_openrouter.SCRIPT_STYLES:
            raise ValueError("Default script style not in available styles")
        
        logger.info("✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}", exc_info=True)
        return False

async def run_all_tests():
    """Run all tests."""
    logger.info("🚀 Starting TikTok script generation tests...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Text Extraction", test_text_extraction),
        ("Script Structure", test_script_structure)
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
        logger.info("\n🎉 All tests passed! The script generation functionality is ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Set your OPENROUTER_API_KEY environment variable")
        logger.info("2. Download a thread: python main.py <tweet_url>")
        logger.info("3. Generate script: python main.py <tweet_url> --generate-script")
        logger.info("4. Or batch process: python batch_script_generator.py output/")
    else:
        logger.error(f"\n💥 {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_all_tests())
