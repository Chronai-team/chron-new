#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test importing all analyzer modules"""
    try:
        from analyzer.market_analyzer import MarketAnalyzer
        print("✓ Successfully imported MarketAnalyzer")
        
        from analyzer.code_analyzer import CodeAnalyzer, AnalysisResult
        print("✓ Successfully imported CodeAnalyzer and AnalysisResult")
        
        from analyzer.authenticity_detector import AuthenticityDetector
        print("✓ Successfully imported AuthenticityDetector")
        
        from analyzer.execution_verifier import ExecutionVerifier
        print("✓ Successfully imported ExecutionVerifier")
        
        from analyzer.report_generator import ReportGenerator
        print("✓ Successfully imported ReportGenerator")
        
        from analyzer.gpt_analyzer import GPTAnalyzer
        print("✓ Successfully imported GPTAnalyzer")
        
        return True
    except Exception as e:
        print(f"Import error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
