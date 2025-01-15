import pytest
import os
import sys
import json
import time
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analyzer.gpt_analyzer import GPTAnalyzer

# Enable asyncio test mode
pytestmark = pytest.mark.asyncio

@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, choices):
        self.choices = choices

class MockHandler:
    """Mock handler for OpenAI API calls"""
    def __init__(self):
        self._call_count = 0
        self.max_calls = int(os.getenv('MAX_GPT_CALLS', '5'))
        self.error_mode = False
        self.error_message = None
        self.reset_time = time.time() + 3600
        self.cache = {}  # Add cache for tracking calls
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = self.create
        print(f"MockHandler initialized with max_calls={self.max_calls}, reset_time={self.reset_time}")
        
    @property
    def call_count(self):
        return self._call_count
        
    async def create(self, *args, **kwargs):
        """Mock OpenAI API call with rate limiting"""
        try:
            # Check rate limit reset
            current_time = time.time()
            if current_time >= self.reset_time:
                print(f"MockHandler: Resetting call count (was {self._call_count})")
                self._call_count = 0  # Reset counter
                self.reset_time = current_time + 3600
                
            # Check if next call would exceed rate limit
            next_count = self._call_count + 1
            if next_count > self.max_calls:
                print(f"MockHandler: Rate limit would be exceeded ({next_count} > {self.max_calls})")
                content = {
                    'ai_score': 0.5,
                    'quality_score': 0.5,
                    'originality_score': 0.5,
                    'execution_score': 0.5,
                    'market_value': 0.5,
                    'findings': ["GPT analysis failed: Rate limit exceeded"],
                    'recommendations': ["Try again later"]
                }
                return MockResponse([MockChoice(MockMessage(json.dumps(content)))])
            
            # Increment counter for valid calls
            self._call_count = next_count
            print(f"MockHandler: call_count incremented to {self._call_count}")
            
            if self.error_mode:
                error_msg = self.error_message or 'API Error'
                content = {
                    'ai_score': 0.5,
                    'quality_score': 0.5,
                    'originality_score': 0.5,
                    'execution_score': 0.5,
                    'market_value': 0.5,
                    'findings': [f"GPT analysis failed: {error_msg}"],
                    'recommendations': ["Check error handling"]
                }
                return MockResponse([MockChoice(MockMessage(json.dumps(content)))])
            
            # Return normal response for successful calls
            print(f"MockHandler: Returning normal response (call {self._call_count}/{self.max_calls})")
            content = {
                'ai_score': 0.8,
                'quality_score': 0.7,
                'originality_score': 0.9,
                'execution_score': 0.6,
                'market_value': 0.85,
                'findings': ["Good AI implementation"],
                'recommendations': ["Consider optimizing further"]
            }
            return MockResponse([MockChoice(MockMessage(json.dumps(content)))])
        except Exception as e:
            print(f"MockHandler: Error in create: {e}")
            # Return fallback response on error
            content = {
                'ai_score': 0.5,
                'quality_score': 0.5,
                'originality_score': 0.5,
                'execution_score': 0.5,
                'market_value': 0.5,
                'findings': [f"GPT analysis failed: {str(e)}"],
                'recommendations': ["Try again later"]
            }
            return MockResponse([MockChoice(MockMessage(json.dumps(content)))])
        
    def set_error_mode(self, enabled=True, message=None):
        self.error_mode = enabled
        self.error_message = message
        
    def get_call_count(self):
        return self._call_count

@pytest.fixture
def mock_handler():
    """Create mock handler for OpenAI API calls"""
    return MockHandler()

@pytest.fixture(autouse=True)
def mock_openai(monkeypatch, mock_handler):
    """Mock OpenAI client"""
    from analyzer.gpt_analyzer import set_test_mock
    
    # Set up both the OpenAI mock and our test mock
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: mock_handler)
    set_test_mock(mock_handler)
    
    return mock_handler

async def test_cache_hit(temp_cache_dir, mock_handler):
    """Test that cached results are returned without calling GPT"""
    # Setup
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = temp_cache_dir
    os.environ['MAX_GPT_CALLS'] = '5'
    
    analyzer = GPTAnalyzer()
    test_code = "def test(): pass"
    
    # First call should use GPT
    result1 = await analyzer.analyze_code_segment(test_code)
    assert mock_handler.call_count == 1, "First call should increment counter"
    assert result1['ai_score'] == 0.8, "First call should return normal response"
    
    # Second call should use cache
    result2 = await analyzer.analyze_code_segment(test_code)
    assert mock_handler.call_count == 1, "Cache hit should not increment counter"
    assert result1 == result2, "Cache hit should return same result"

async def test_cache_ttl(temp_cache_dir, mock_handler):
    """Test that expired cache entries trigger new GPT calls"""
    # Setup with very short TTL
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = temp_cache_dir
    os.environ['GPT_CACHE_TTL'] = '1'  # 1 second TTL
    os.environ['MAX_GPT_CALLS'] = '5'
    
    analyzer = GPTAnalyzer()
    test_code = "def test(): pass"
    
    # First call
    result1 = await analyzer.analyze_code_segment(test_code)
    assert mock_handler.call_count == 1, "First call should increment counter"
    assert result1['ai_score'] == 0.8, "First call should return normal response"
    
    # Wait for cache to expire
    await asyncio.sleep(2)
    
    # Second call should trigger new GPT call
    result2 = await analyzer.analyze_code_segment(test_code)
    assert mock_handler.call_count == 2, "Expired cache should trigger new call"
    assert result2['ai_score'] == 0.8, "Second call should return normal response"

async def test_rate_limit(temp_cache_dir, mock_handler):
    """Test that rate limiting prevents excessive GPT calls"""
    # Setup with low rate limit (2 calls max)
    os.environ.clear()  # Clear any existing environment variables
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = temp_cache_dir
    os.environ['MAX_GPT_CALLS'] = '2'
    
    analyzer = GPTAnalyzer()
    
    # First call - should succeed (count = 1)
    result1 = await analyzer.analyze_code_segment("def test1(): pass")
    assert result1['ai_score'] == 0.8, "First call should return normal response"
    assert mock_handler.call_count == 1, "First call should increment counter to 1"
    
    # Second call - should succeed (count = 2)
    result2 = await analyzer.analyze_code_segment("def test2(): pass")
    assert result2['ai_score'] == 0.8, "Second call should return normal response"
    assert mock_handler.call_count == 2, "Second call should increment counter to 2"
    
    # Third call - should hit rate limit (count = 2, next_call would be 3)
    result3 = await analyzer.analyze_code_segment("def test3(): pass")
    assert result3['ai_score'] == 0.5, "Rate limited call should return fallback"
    assert mock_handler.call_count == 2, "Call count should not increment for rate limited calls"

async def test_rate_limit_reset(temp_cache_dir, mock_handler):
    """Test that rate limit counter resets after an hour"""
    # Setup
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = temp_cache_dir
    os.environ['MAX_GPT_CALLS'] = '1'
    
    analyzer = GPTAnalyzer()
    
    # Use up rate limit
    result1 = await analyzer.analyze_code_segment("def test1(): pass")
    assert mock_handler.call_count == 1, "First call should increment counter"
    assert result1['ai_score'] == 0.8, "First call should return normal response"
    
    # Simulate time passing
    analyzer.call_reset_time = 0  # Force reset
    
    # Should be able to make another call
    result2 = await analyzer.analyze_code_segment("def test2(): pass")
    assert mock_handler.call_count == 2, "Reset should allow new call"
    assert result2['ai_score'] == 0.8, "Post-reset call should return normal response"

async def test_missing_api_key():
    """Test that analyzer fails gracefully without API key"""
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    with pytest.raises(ValueError, match="OpenAI API key not found"):
        GPTAnalyzer()

async def test_gpt_error_handling(temp_cache_dir, mock_handler):
    """Test handling of GPT API errors"""
    # Setup
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GPT_ANALYSIS_CACHE_PATH'] = temp_cache_dir
    os.environ['MAX_GPT_CALLS'] = '5'
    
    analyzer = GPTAnalyzer()
    
    # Make GPT call fail
    mock_handler.set_error_mode(True, "API Error")
    
    # Should get fallback response
    result = await analyzer.analyze_code_segment("def test(): pass")
    assert result['ai_score'] == 0.5, "Error should trigger fallback score"
    assert "GPT analysis failed" in result['findings'][0], "Error should be reported in findings"
