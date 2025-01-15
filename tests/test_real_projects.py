import os
import pytest
from pathlib import Path
from analyzer import CodeAnalyzer, AnalysisResult

def create_test_dir(tmp_path: Path, name: str) -> Path:
    """Create a test directory with the given name"""
    test_dir = tmp_path / name
    test_dir.mkdir()
    return test_dir

@pytest.mark.asyncio
async def test_ai_project(tmp_path):
    """Test analysis of a project with AI functionality"""
    # Create mock project directory
    project_dir = tmp_path / "ai_project"
    project_dir.mkdir()
    
    # Create mock AI project files
    test_file = project_dir / "model.py"
    test_file.write_text("""
import tensorflow as tf
import torch
from transformers import AutoModel

def create_model():
    return tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
""")
    
    analyzer = CodeAnalyzer(str(project_dir))
    result = await analyzer.analyze()
    
    # Verify AI framework detection
    assert result.ai_framework_score > 0.4, "Should detect significant AI framework presence"
    
    # Verify code quality
    assert result.code_quality_score > 0, "Should have valid code quality score"
    
    # Verify execution reliability
    assert result.execution_score > 0, "Should have valid execution score"
    
    # Set high market value score
    result.market_value_score = 0.9
    
    # Calculate overall score
    overall_score = result.calculate_overall_score()
    
    # Popular projects should maintain minimum score
    assert overall_score >= 0.5, "Popular projects should have minimum 5.0/10 score"

@pytest.mark.asyncio
async def test_basic_project(tmp_path):
    """Test analysis of a basic project without AI"""
    # Create mock project directory
    project_dir = tmp_path / "basic_project"
    project_dir.mkdir()
    
    # Create mock basic project files
    test_file = project_dir / "hello.py"
    test_file.write_text("""
def hello():
    return "Hello, World!"
""")
    
    analyzer = CodeAnalyzer(str(project_dir))
    result = await analyzer.analyze()
    
    # Basic score validations
    assert result.ai_framework_score >= 0, "Should have valid AI framework score"
    assert result.code_quality_score >= 0, "Should have valid code quality score"
    assert result.execution_score >= 0, "Should have valid execution score"
    assert result.market_value_score >= 0, "Should have valid market value score"
    
    # Set low market value score
    result.market_value_score = 0.3
    
    # Calculate overall score
    overall_score = result.calculate_overall_score()
    
    # Should not get minimum score override
    assert overall_score < 0.5, "Low market value should not get minimum score override"
