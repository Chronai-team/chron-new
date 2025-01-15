import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = '/tmp/chronai/test_cache'
    os.environ['MAX_GPT_CALLS'] = '5'
    os.environ['GPT_CACHE_TTL'] = '3600'
    yield
    # Clean up
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
