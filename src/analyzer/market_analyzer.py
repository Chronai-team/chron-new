"""
Market Value Analyzer for AI Projects
===================================

Analyzes project market success and popularity using multiple metrics:
1. GitHub metrics (stars, forks, contributors)
2. Community adoption and engagement
3. Industry recognition and impact
4. Market presence and growth trends

Provides weighted scoring with exact 30% contribution to overall project score.
Popular projects (market_value >= 0.8) receive minimum 5.0/10 score boost.

Features:
- GPT-powered market research
- Caching system for API efficiency
- Configurable scoring thresholds
- Detailed market metrics and recommendations
"""
import os
import json
import time
import logging
from typing import Dict, Optional
from pathlib import Path
from .gpt_analyzer import GPTAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MarketAnalyzer:
    """Analyzes project market success and popularity"""
    
    def __init__(self):
        """Initialize market analyzer with GPT integration"""
        self.gpt_analyzer = GPTAnalyzer()
        
        # Configure caching
        cache_path = os.getenv('GPT_ANALYSIS_CACHE_PATH')
        if cache_path:
            self.cache_dir = Path(cache_path) / 'market'
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None
            
        # Cache TTL in seconds (default 24 hours)
        self.cache_ttl = int(os.getenv('MARKET_CACHE_TTL', str(24 * 3600)))
        
        # Popularity thresholds
        self.popularity_threshold = int(os.getenv('POPULARITY_THRESHOLD', '1000'))
        self.min_popular_score = float(os.getenv('MIN_POPULAR_SCORE', '5.0')) / 10.0
        
    async def analyze_market_value(self, project_name: str, repo_url: str) -> Dict:
        """
        Analyze project's market value and popularity
        Returns a dict with market metrics
        """
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
            # Get market analysis from GPT
            market_data = await self.gpt_analyzer.analyze_market_context(
                project_name=project_name,
                repo_url=repo_url
            )
            
            # Calculate normalized market score
            market_score = self._calculate_market_score(market_data)
            
            result = {
                'market_score': market_score,
                'is_popular': market_score >= 0.8,
                'popularity_metrics': market_data.get('popularity_metrics', {}),
                'community_metrics': market_data.get('community_metrics', {}),
                'market_context': market_data.get('market_context', ''),
                'recommendations': market_data.get('recommendations', [])
            }
            
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
            return self._get_fallback_analysis()
            
    def _calculate_market_score(self, market_data: Dict) -> float:
        """Calculate normalized market score from analysis data"""
        try:
            # Extract metrics
            popularity = float(market_data.get('popularity_score', 0.5))
            adoption = float(market_data.get('adoption_score', 0.5))
            impact = float(market_data.get('impact_score', 0.5))
            
            # Weight the components
            weighted_score = (
                popularity * 0.4 +  # GitHub stars, forks
                adoption * 0.4 +    # Industry adoption
                impact * 0.2        # Market impact
            )
            
            return min(1.0, weighted_score)
            
        except Exception as e:
            logging.error(f"Error calculating market score: {e}")
            return 0.5
            
    def _get_fallback_analysis(self) -> Dict:
        """Get fallback analysis when market research fails"""
        return {
            'market_score': 0.5,
            'is_popular': False,
            'popularity_metrics': {},
            'community_metrics': {},
            'market_context': 'Market analysis unavailable',
            'recommendations': ['Enable market analysis for enhanced results']
        }
        
    def should_boost_score(self, market_score: float) -> bool:
        """Determine if project score should be boosted based on popularity"""
        return market_score >= 0.8
        
    def get_minimum_score(self, market_score: float) -> Optional[float]:
        """Get minimum score threshold based on market success"""
        if market_score >= 0.8:
            return self.min_popular_score
        elif market_score >= 0.6:
            return 0.4  # 4.0/10 for moderately popular projects
        return None  # No minimum for other projects
