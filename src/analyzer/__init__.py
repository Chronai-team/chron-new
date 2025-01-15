"""
Chronai AI Project Analysis Tool - Core Analyzer Package
"""
import logging
import asyncio

from .code_analyzer import CodeAnalyzer, AnalysisResult
from .authenticity_detector import AuthenticityDetector
from .execution_verifier import ExecutionVerifier
from .report_generator import ReportGenerator, Report
from .gpt_analyzer import GPTAnalyzer
from .market_analyzer import MarketAnalyzer

__all__ = [
    'CodeAnalyzer',
    'AnalysisResult',
    'AuthenticityDetector',
    'ExecutionVerifier',
    'ReportGenerator',
    'Report',
    'GPTAnalyzer',
    'MarketAnalyzer'
]

# Configure logging
logging.basicConfig(level=logging.INFO)

# Let pytest-asyncio handle the event loop
# This avoids the "no current event loop" warning
if not asyncio._get_running_loop():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception as e:
        logging.warning(f"Failed to set event loop: {e}")
        # Let pytest-asyncio handle it
