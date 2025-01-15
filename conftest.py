import pytest
import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_dir = str(project_root / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = '/tmp/test_cache'
    os.environ['MAX_GPT_CALLS'] = '5'
    os.environ['GPT_CACHE_TTL'] = '3600'
    os.environ['MARKET_CACHE_TTL'] = '3600'
    os.environ['MIN_POPULAR_SCORE'] = '5.0'
    yield
    # Clean up
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
