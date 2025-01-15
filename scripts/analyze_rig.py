#!/usr/bin/env python3
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.append(src_dir)

from analyzer import CodeAnalyzer

async def main():
    """Analyze the Rig repository using Chron AI analyzer"""
    try:
        print("\nStarting Rig Analysis...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        repo_url = os.getenv('RIG_REPO', 'https://github.com/0xPlaygrounds/rig')
        analyzer = CodeAnalyzer(repo_url)
        result = await analyzer.analyze()
        
        # Calculate overall score with market value contribution
        overall_score = result.calculate_overall_score()
        
        # Convert scores to 10-point scale
        ai_score = result.ai_framework_score * 10
        code_score = result.code_quality_score * 10
        exec_score = result.execution_score * 10
        market_score = result.market_value_score * 10
        originality_score = result.security_score * 10  # Using security score for originality
        overall_score = overall_score * 10
        
        # Print detailed analysis results
        print("## Chron AI Analysis Results\n")
        print("### Component Scores (0-10 scale)")
        print("1. AI Framework Implementation")
        print(f"   Score: {ai_score:.1f}/10")
        print("   Evaluates: AI model integration, prompt engineering, context handling")
        print("\n2. Code Quality & Patterns")
        print(f"   Score: {code_score:.1f}/10")
        print("   Evaluates: AI-specific patterns, documentation, error handling")
        print("\n3. Execution & Performance")
        print(f"   Score: {exec_score:.1f}/10")
        print("   Evaluates: Runtime efficiency, resource management, reliability")
        print("\n4. Market Success")
        print(f"   Score: {market_score:.1f}/10")
        print("   Evaluates: Project popularity, community adoption, market impact")
        print("\n5. Code Originality")
        print(f"   Score: {originality_score:.1f}/10")
        print("   Evaluates: Code uniqueness, implementation originality, framework customization")
        print("\n### Overall Project Score")
        print(f"Final Score: {overall_score:.1f}/10")
        print("Weight Distribution: 30/20/20/20/10 (Market/AI/Code/Execution/Originality)\n")
        
        if result.issues:
            print("### Issues Identified")
            for issue in result.issues:
                print(f"- {issue}")
            print()
            
        if result.recommendations:
            print("### Recommendations")
            for rec in result.recommendations:
                print(f"- {rec}")
            print()
            
        print("\nAnalysis completed successfully.")
        return 0
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
