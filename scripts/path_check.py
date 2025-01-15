#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def check_paths():
    """Check Python paths and verify imports"""
    print("=== Python Path Check ===")
    print("\nCurrent Directory:", os.getcwd())
    print("\nPython Path:")
    for path in sys.path:
        print(f"  {path}")
        
    print("\nProject Files:")
    project_root = Path(__file__).parent.parent
    for path in project_root.rglob("*.py"):
        print(f"  {path.relative_to(project_root)}")
        
    print("\nTrying imports...")
    try:
        import analyzer
        from analyzer.market_analyzer import MarketAnalyzer
        print("✓ Successfully imported analyzer modules")
        return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_paths()
    sys.exit(0 if success else 1)
