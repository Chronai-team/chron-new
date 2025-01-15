#!/usr/bin/env python3
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add the src directory to Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.append(src_dir)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    print(f"Error: .env file not found at {env_path}")
    sys.exit(1)
load_dotenv(env_path)

def verify_environment():
    """Verify that all required components are available"""
    try:
        # Check imports
        print("Checking imports...")
        from analyzer import (
            CodeAnalyzer,
            AuthenticityDetector,
            ExecutionVerifier,
            ReportGenerator
        )
        print("✓ Successfully imported all analyzer components")

        # Check environment variables
        print("\nChecking environment variables...")
        required_vars = [
            'OPENAI_API_KEY',
            'MAX_GPT_CALLS',
            'GPT_ANALYSIS_CACHE_PATH',
            'GPT_CACHE_TTL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print("⚠ Missing environment variables:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease set these variables in your .env file")
            return 1
        else:
            print("✓ All required environment variables are set")

        print("\nEnvironment verification completed successfully.")
        return 0
        
    except ImportError as e:
        print(f"\nEnvironment verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(verify_environment())
