#!/usr/bin/env python3
import sys

def clean_paths():
    """Remove chronai paths from sys.path"""
    sys.path = [p for p in sys.path if 'chronai' not in p]
    
if __name__ == "__main__":
    clean_paths()
    from analyzer import CodeAnalyzer, AnalysisResult
    print("Imports successful!")
