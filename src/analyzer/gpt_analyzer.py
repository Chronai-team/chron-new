import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from openai import OpenAI

# Global test mock
_test_mock = None

def set_test_mock(mock):
    """Set the global test mock for GPTAnalyzer"""
    global _test_mock
    _test_mock = mock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class GPTAnalyzer:
    """Uses GPT to enhance code analysis capabilities with caching and rate limiting"""
    
    def __init__(self):
        # Get API key and set test mode
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment")
            
        # Configure rate limiting first - always use environment value
        self.max_calls = int(os.getenv('MAX_GPT_CALLS', '5'))
        self.calls_made = 0
        self.call_reset_time = time.time() + 3600  # Reset counter every hour
        print(f"GPTAnalyzer initialized with max_calls={self.max_calls}")
        
        # Set test mode if using test key (after rate limit config)
        self.is_test = api_key == 'test-key'
        
        # Configure caching
        cache_path = os.getenv('GPT_ANALYSIS_CACHE_PATH')
        if cache_path:
            self.cache_dir = Path(cache_path)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None
            
        # Cache TTL in seconds (default 24 hours)
        self.cache_ttl = int(os.getenv('GPT_CACHE_TTL', str(24 * 3600)))
        
        # Initialize OpenAI client
        if self.is_test:
            # Use provided test mock or create default
            if _test_mock is not None:
                self.client = _test_mock
                print(f"Using provided test mock with max_calls={self.max_calls}")
            else:
                # Create default mock with async support
                mock = MagicMock()
                mock.chat = MagicMock()
                mock.chat.completions = MagicMock()
                
                # Create different responses based on the prompt content
                async def mock_create(**kwargs):
                    messages = kwargs.get('messages', [])
                    user_content = messages[-1]['content'] if messages else ""
                    
                    if "market success" in user_content.lower():
                        # Market analysis response
                        content = {
                            'popularity_score': 0.85,
                            'adoption_score': 0.80,
                            'impact_score': 0.75,
                            'popularity_metrics': {
                                'stars': 1200,
                                'forks': 150,
                                'watchers': 300
                            },
                            'community_metrics': {
                                'contributors': 25,
                                'issues': 150,
                                'pull_requests': 200
                            },
                            'market_context': "Strong community engagement and adoption",
                            'recommendations': ["Consider enterprise support options"]
                        }
                    else:
                        # Code analysis response
                        content = {
                            'ai_score': 0.8,
                            'quality_score': 0.7,
                            'originality_score': 0.9,
                            'execution_score': 0.6,
                            'market_value': 0.85,
                            'findings': ["Good AI implementation"],
                            'recommendations': ["Consider optimizing further"]
                        }
                    
                    return MagicMock(
                        choices=[MagicMock(message=MagicMock(
                            content=json.dumps(content)
                        ))]
                    )
                
                mock.chat.completions.create = AsyncMock(side_effect=mock_create)
                self.client = mock
                print("Using default test mock")
        else:
            self.client = OpenAI(api_key=api_key)
        
    async def analyze_code_segment(self, code: str, context: str = "") -> Dict:
        """Analyze a code segment using GPT with caching"""
        cache_key = f"analyze_{hash(code + context)}"
        
        # Check cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                # Check cache age
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < self.cache_ttl:
                    try:
                        with open(cache_file, 'r') as f:
                            return json.load(f)
                    except json.JSONDecodeError:
                        # Invalid cache, will recompute
                        pass
                        
        # Check rate limit reset
        current_time = time.time()
        if current_time >= self.call_reset_time:
            self.calls_made = 0
            self.call_reset_time = current_time + 3600
            
        # Check if next call would exceed rate limit
        next_count = self.calls_made + 1
        print(f"GPTAnalyzer: calls_made={self.calls_made}, max_calls={self.max_calls}, next_count={next_count}")
        if next_count > self.max_calls:
            print("GPTAnalyzer: Rate limit would be exceeded, returning fallback")
            logging.warning("GPT API rate limit would be exceeded. Using fallback analysis.")
            return self._get_fallback_analysis("Rate limit reached")
            
        # Increment counter before making the call
        print(f"GPTAnalyzer: Incrementing calls_made to {next_count}")
        self.calls_made = next_count
        
        try:
            # Make API call
            # Create completion with proper async handling
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert code analyzer focused on:
1. Identifying AI/ML implementations
2. Detecting code quality issues
3. Finding potential plagiarism
4. Assessing code executability

Provide analysis in JSON format with these keys:
- ai_score: float 0-1
- quality_score: float 0-1
- originality_score: float 0-1
- execution_score: float 0-1
- market_value: float 0-1
- findings: list of strings
- recommendations: list of strings"""},
                    {"role": "user", "content": f"Context: {context}\n\nAnalyze this code:\n```\n{code}\n```"}
                ]
            )
            
            # Parse the response with better error handling
            try:
                content = response.choices[0].message.content
                # Clean up potential formatting issues
                content = content.strip()
                if not content.startswith('{'):
                    # Try to find the JSON object
                    start = content.find('{')
                    end = content.rfind('}')
                    if start >= 0 and end > start:
                        content = content[start:end+1]
                    else:
                        raise ValueError("No valid JSON object found in response")
                
                analysis = json.loads(content)
                result = {
                    'ai_score': float(analysis.get('ai_score', 0.5)),
                    'quality_score': float(analysis.get('quality_score', 0.5)),
                    'originality_score': float(analysis.get('originality_score', 0.5)),
                    'execution_score': float(analysis.get('execution_score', 0.5)),
                    'market_value': float(analysis.get('market_value', 0.5)),
                    'findings': analysis.get('findings', ["No findings available"]),
                    'recommendations': analysis.get('recommendations', ["No recommendations available"])
                }
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse GPT response: {e}\nResponse content: {content}")
                return self._get_fallback_analysis(f"JSON parse error: {str(e)}")
            except Exception as e:
                logging.error(f"Error processing GPT response: {e}")
                return self._get_fallback_analysis(str(e))
            
            # Cache the result if caching is enabled
            if self.cache_dir:
                try:
                    with open(self.cache_dir / f"{cache_key}.json", 'w') as f:
                        json.dump(result, f)
                except Exception as e:
                    logging.warning(f"Failed to cache analysis: {e}")
                    
            return result
            
        except Exception as e:
            logging.error(f"GPT analysis failed: {str(e)}")
            return self._get_fallback_analysis(str(e))
            
    def _get_fallback_analysis(self, error_msg: str) -> Dict:
        """Get fallback analysis result when GPT fails"""
        return {
            'ai_score': 0.5,
            'quality_score': 0.5,
            'originality_score': 0.5,
            'execution_score': 0.5,
            'market_value': 0.5,
            'findings': [f"GPT analysis failed: {error_msg}"] if error_msg else ["No findings available"],
            'recommendations': ["Enable GPT analysis for enhanced results"]
        }
        

        
    async def verify_ai_implementation(self, code: str) -> Dict:
        """Specifically verify if code implements real AI/ML functionality with caching"""
        # Check rate limit reset
        current_time = time.time()
        if current_time >= self.call_reset_time:
            self.calls_made = 0
            self.call_reset_time = current_time + 3600
            
        # Check if we've reached the rate limit
        if self.calls_made >= self.max_calls:
            logging.warning("GPT API rate limit reached. Using fallback verification.")
            return {
                'is_real_ai': False,
                'implementation_type': 'unknown',
                'confidence': 0.0,
                'evidence': ["Rate limit reached"],
                'suggestions': ["Try again later"]
            }
            
        # Increment counter for successful calls
        self.calls_made += 1

        cache_key = f"verify_{hash(code)}"
        
        # Check cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < self.cache_ttl:
                    try:
                        with open(cache_file, 'r') as f:
                            return json.load(f)
                    except json.JSONDecodeError:
                        pass
                        
        try:
            # Rate limit already checked before this point
                    
            # Create completion with proper async handling
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert at identifying genuine AI/ML implementations.
Focus on distinguishing between:
1. Real ML model implementations
2. Basic API calls to AI services
3. Framework-level AI code
4. Simple prompt engineering

Provide analysis in JSON format with:
- is_real_ai: boolean
- implementation_type: string (framework|api|hybrid|none)
- confidence: float 0-1
- evidence: list of strings
- suggestions: list of strings"""},
                    {"role": "user", "content": f"Analyze this code for AI implementation:\n```\n{code}\n```"}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result if caching is enabled
            if self.cache_dir:
                try:
                    with open(self.cache_dir / f"{cache_key}.json", 'w') as f:
                        json.dump(result, f)
                except Exception as e:
                    logging.warning(f"Failed to cache verification: {e}")
                    
            return result
            
        except Exception as e:
            logging.error(f"AI verification failed: {str(e)}")
            return {
                'is_real_ai': False,
                'implementation_type': 'unknown',
                'confidence': 0.0,
                'evidence': [f"Analysis failed: {str(e)}"],
                'suggestions': ["Enable GPT analysis for AI verification"]
            }
            
    async def analyze_market_context(self, project_name: str, repo_url: str) -> Dict:
        """Analyze market context and popularity of a project"""
        cache_key = f"market_{hash(project_name + repo_url)}"
        
        # Check cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < self.cache_ttl:
                    try:
                        with open(cache_file, 'r') as f:
                            return json.load(f)
                    except json.JSONDecodeError:
                        pass
                        
        try:
            # Create completion with proper async handling
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert at analyzing AI project market success.
Focus on:
1. Project popularity (GitHub stars, forks)
2. Community adoption and engagement
3. Industry recognition and impact
4. Market presence and growth

Provide analysis in JSON format with:
- popularity_score: float 0-1
- adoption_score: float 0-1
- impact_score: float 0-1
- popularity_metrics: object
- community_metrics: object
- market_context: string
- recommendations: list of strings"""},
                    {"role": "user", "content": f"Analyze market success for project {project_name} ({repo_url})"}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result if caching is enabled
            if self.cache_dir:
                try:
                    with open(self.cache_dir / f"{cache_key}.json", 'w') as f:
                        json.dump(result, f)
                except Exception as e:
                    logging.warning(f"Failed to cache market analysis: {e}")
                    
            return result
            
        except Exception as e:
            logging.error(f"Market analysis failed: {str(e)}")
            return {
                'popularity_score': 0.5,
                'adoption_score': 0.5,
                'impact_score': 0.5,
                'popularity_metrics': {},
                'community_metrics': {},
                'market_context': f"Analysis failed: {str(e)}",
                'recommendations': ["Enable GPT analysis for market research"]
            }
            
    async def check_code_originality(self, code: str) -> Dict:
        """Use GPT to detect potential code plagiarism or common patterns with caching"""
        # Check rate limit reset
        current_time = time.time()
        if current_time >= self.call_reset_time:
            self.calls_made = 0
            self.call_reset_time = current_time + 3600
            
        # Check if we've reached the rate limit
        if self.calls_made >= self.max_calls:
            logging.warning("GPT API rate limit reached. Using fallback originality check.")
            return {
                'originality_score': 0.5,
                'is_likely_copied': False,
                'common_patterns': ["Rate limit reached"],
                'unique_elements': [],
                'recommendations': ["Try again later"]
            }
            
        # Increment counter for successful calls
        self.calls_made += 1

        cache_key = f"originality_{hash(code)}"
        
        # Check cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < self.cache_ttl:
                    try:
                        with open(cache_file, 'r') as f:
                            return json.load(f)
                    except json.JSONDecodeError:
                        pass
                        
        try:
            # Rate limit already checked before this point
                    
            # Create completion with proper async handling
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert at identifying code originality and potential plagiarism.
Focus on:
1. Common code patterns vs unique implementations
2. Framework-specific boilerplate
3. Copied documentation or comments
4. Unique algorithmic approaches

Provide analysis in JSON format with:
- originality_score: float 0-1
- is_likely_copied: boolean
- common_patterns: list of strings
- unique_elements: list of strings
- recommendations: list of strings"""},
                    {"role": "user", "content": f"Analyze this code for originality:\n```\n{code}\n```"}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result if caching is enabled
            if self.cache_dir:
                try:
                    with open(self.cache_dir / f"{cache_key}.json", 'w') as f:
                        json.dump(result, f)
                except Exception as e:
                    logging.warning(f"Failed to cache originality check: {e}")
                    
            return result
            
        except Exception as e:
            logging.error(f"Originality check failed: {str(e)}")
            return {
                'originality_score': 0.5,
                'is_likely_copied': False,
                'common_patterns': [],
                'unique_elements': [],
                'recommendations': ["Enable GPT analysis for originality verification"]
            }
