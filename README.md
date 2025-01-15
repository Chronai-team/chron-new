# Chron AI - AI Project Analyzer

Chron AI is a sophisticated analysis tool for evaluating AI/ML projects, providing comprehensive assessments across multiple dimensions including market success, technical implementation, and code quality.

## Features

- **Multi-Dimensional Analysis**: Evaluates projects across 5 key dimensions
- **Market Value Integration**: GPT-powered market research and community analysis
- **Multi-Language Support**: Analyzes Python, Rust, TypeScript/JavaScript codebases
- **Comprehensive Reporting**: Detailed analysis reports with actionable recommendations
- **Automated Scoring**: Standardized evaluation framework with weighted scoring

## Scoring System

Our analysis uses a weighted scoring system:
- Market Success (30%): Community adoption, market presence, growth trends
- AI Framework Implementation (20%): LLM integration, prompt engineering, context handling
- Code Quality (20%): Documentation, error handling, test coverage
- Execution Performance (20%): Resource management, optimization, reliability
- Code Originality (10%): Implementation uniqueness, architectural innovation

Projects with high market value (≥ 0.8) receive a minimum overall score of 5.0/10.

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install package
pip install -e .
```

## Configuration

1. Create `.env` file from template:
```bash
cp .env.example .env
```

2. Configure required API keys:
```env
OPENAI_API_KEY=your_key_here
GPT_ANALYSIS_CACHE_PATH=/path/to/cache
MAX_GPT_CALLS=5
GPT_CACHE_TTL=3600
```

## Usage

### Command Line Interface

```bash
# Analyze a GitHub repository
python scripts/analyze_project.py --repo https://github.com/user/repo

# Generate comparative analysis
python scripts/analyze_multiple.py --repos repo1_url repo2_url
```

### Python API

```python
from analyzer import CodeAnalyzer

async def analyze_project(repo_url: str):
    analyzer = CodeAnalyzer(repo_url)
    result = await analyzer.analyze()
    
    # Access component scores
    print(f"Market Score: {result.market_value_score * 10}/10")
    print(f"AI Score: {result.ai_framework_score * 10}/10")
    print(f"Code Score: {result.code_quality_score * 10}/10")
    print(f"Execution Score: {result.execution_score * 10}/10")
    print(f"Originality Score: {result.security_score * 10}/10")
    
    # Calculate overall score
    overall = result.calculate_overall_score() * 10
    print(f"Overall Score: {overall}/10")
```

## Components

### Core Analyzers

- **CodeAnalyzer**: Main analysis coordinator
- **MarketAnalyzer**: Evaluates market success and community adoption
- **GPTAnalyzer**: Provides AI-powered code and market analysis
- **AuthenticityDetector**: Validates AI framework implementations
- **ExecutionVerifier**: Assesses runtime performance and reliability
- **ReportGenerator**: Creates detailed analysis reports

### Analysis Reports

Reports are generated in markdown format and include:
- Executive Summary
- Component Analysis
- Detailed Findings
- Technical Implementation Details
- Recommendations

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Adding New Analyzers

1. Create new analyzer in `src/analyzer/`
2. Implement required interface:
```python
class NewAnalyzer:
    async def analyze(self) -> float:
        """Perform analysis and return score 0-1"""
        pass
```
3. Add tests in `tests/`
4. Update `CodeAnalyzer` to integrate new component

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

MIT License - See LICENSE file for details
