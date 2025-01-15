import pytest
from unittest.mock import MagicMock, AsyncMock
from analyzer.market_analyzer import MarketAnalyzer
from analyzer.code_analyzer import AnalysisResult
from analyzer.report_generator import ReportGenerator
from analyzer.gpt_analyzer import GPTAnalyzer

@pytest.fixture
def mock_gpt_analyzer():
    mock = MagicMock(spec=GPTAnalyzer)
    mock.analyze_market_context = AsyncMock(return_value={
        'popularity_score': 0.9,
        'adoption_score': 0.9,
        'impact_score': 0.9,
        'popularity_metrics': {'stars': 5000, 'forks': 500},
        'community_metrics': {'contributors': 50, 'issues': 200},
        'market_context': 'High adoption and community engagement',
        'recommendations': ['Consider enterprise support'],
        'market_score': 0.9  # Ensure consistent market score
    })
    return mock

@pytest.fixture
def market_analyzer(mock_gpt_analyzer):
    analyzer = MarketAnalyzer()
    analyzer.gpt_analyzer = mock_gpt_analyzer
    return analyzer

@pytest.fixture
def mock_gpt_response():
    return {
        'popularity_score': 0.9,
        'adoption_score': 0.8,
        'impact_score': 0.7,
        'popularity_metrics': {'stars': 5000, 'forks': 500},
        'community_metrics': {'contributors': 50, 'issues': 200},
        'market_context': 'High adoption and community engagement',
        'recommendations': ['Consider enterprise support']
    }

@pytest.mark.asyncio
async def test_market_score_calculation(market_analyzer, mock_gpt_response):
    """Test market score calculation with weighted components"""
    score = market_analyzer._calculate_market_score(mock_gpt_response)
    assert score > 0.8, "Popular project should have high market score"
    assert score <= 1.0, "Market score should be normalized to 1.0"

@pytest.mark.asyncio
async def test_minimum_score_threshold(market_analyzer):
    """Test minimum score threshold for popular projects"""
    high_score = market_analyzer.get_minimum_score(0.9)
    assert high_score == market_analyzer.min_popular_score
    assert high_score >= 0.5, "Popular projects should have minimum 5.0/10 score"

    med_score = market_analyzer.get_minimum_score(0.7)
    assert med_score == 0.4, "Moderately popular projects should have 4.0/10 minimum"

    low_score = market_analyzer.get_minimum_score(0.3)
    assert low_score is None, "Low popularity should not have minimum score"

@pytest.mark.asyncio
async def test_market_score_integration(market_analyzer):
    """Test integration of market score with overall analysis"""
    # Create analysis result with high market value
    result = AnalysisResult(
        code_quality_score=0.3,
        ai_framework_score=0.4,
        execution_score=0.3,
        security_score=0.3,
        market_value_score=0.9  # Set high market value for testing
    )
    
    # Generate report
    report_gen = ReportGenerator(result)
    report = report_gen.generate_summary()
    
    # Verify minimum score override
    assert report.overall_score >= 0.5, "High market value should ensure minimum 5.0/10"
    assert 'Market Success' in report.detailed_scores
    assert abs(report.detailed_scores['Market Success'] - 0.9) < 0.001
    
    # Verify override notification
    override_note = any('minimum 5.0/10' in rec for rec in report.recommendations)
    assert override_note, "Should include score override notification"

@pytest.mark.asyncio
async def test_market_score_weights():
    """Test market value weight in overall score calculation"""
    result = AnalysisResult(
        code_quality_score=1.0,
        ai_framework_score=1.0,
        execution_score=1.0,
        security_score=1.0,
        market_value_score=1.0
    )
    
    report_gen = ReportGenerator(result)
    report = report_gen.generate_summary()
    
    # With all perfect scores, overall should be 1.0
    assert abs(report.overall_score - 1.0) < 0.001, "Perfect scores should result in 1.0"
    
    # Test with only market value (all other scores 0)
    result = AnalysisResult(
        code_quality_score=0.0,
        ai_framework_score=0.0,
        execution_score=0.0,
        security_score=0.0,
        market_value_score=1.0  # Perfect market value
    )
    
    report_gen = ReportGenerator(result)
    report = report_gen.generate_summary()
    
    # When all base scores are 0, market value should contribute its full 30%
    expected_score = 0.3  # 30% of 1.0
    assert abs(report.overall_score - expected_score) < 0.001, "Market value should contribute exactly 30%"
