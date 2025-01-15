import os
import re
import logging
from git import Repo
from typing import Dict, List, Optional, Union
import radon.complexity as radon_cc
from radon.raw import analyze
from radon.metrics import h_visit
from .gpt_analyzer import GPTAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)

class AnalysisResult:
    """Analysis result with scores and recommendations"""
    
    def __init__(self, code_quality_score: float = 0.0,
                 ai_framework_score: float = 0.0,
                 execution_score: float = 0.0,
                 security_score: float = 0.0,
                 market_value_score: float = 0.0,
                 issues: Optional[List[Dict[str, Union[str, float]]]] = None,
                 recommendations: Optional[List[str]] = None):
        # Initialize scores with type conversion
        self.code_quality_score = float(code_quality_score)
        self.ai_framework_score = float(ai_framework_score)
        self.execution_score = float(execution_score)
        self.security_score = float(security_score)  # Used for originality score
        self.market_value_score = float(market_value_score)  # Market success score
        
        # Initialize lists
        self.issues = issues if issues is not None else []
        self.recommendations = recommendations if recommendations is not None else []
        
        # Define weights as instance attribute
        self.weights = {
            'ai_framework': 0.25,  # AI Implementation Authenticity
            'code_quality': 0.25,  # Code Feasibility
            'execution': 0.25,     # Execution Performance
            'security': 0.25       # Code Originality
        }
        # Market value is handled separately for score boosting
        
        logging.info(f"AnalysisResult initialized with scores: {self.code_quality_score}, {self.ai_framework_score}, {self.execution_score}, {self.security_score}")

    def calculate_overall_score(self) -> float:
        """Calculate overall score with market value boost"""
        try:
            # Get valid base scores (non-zero)
            base_scores = [
                score for score in [
                    self.ai_framework_score,
                    self.code_quality_score,
                    self.execution_score,
                    self.security_score
                ] if score > 0
            ]
            
            # Calculate market contribution (always exactly 30%)
            market_contribution = self.market_value_score * 0.3
            
            # Calculate base score (up to 70%)
            if base_scores:
                # First normalize base scores to 0-1 range
                normalized_base = sum(base_scores) / len(base_scores)
                # Then apply 70% weight
                base_score = normalized_base * 0.7
                
                # For high market success (>= 0.8), ensure minimum total score of 0.5
                # but only if we have valid base scores
                if self.market_value_score >= 0.8:
                    # Calculate minimum required base score
                    min_base = 0.5 - market_contribution
                    base_score = max(base_score, min_base)
                    logging.info(f"Applied minimum score adjustment for high market value")
            else:
                # When no base scores, only use market contribution
                base_score = 0.0
            
            # Calculate total score (market value always contributes exactly 30%)
            score = base_score + market_contribution
            
            logging.info(f"Calculated overall score: {score}")
            return score
        except Exception as e:
            logging.error(f"Error calculating overall score: {e}")
            return 0.0

class CodeAnalyzer:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_path = None
        self.gpt_analyzer = None
        self.market_analyzer = None
        
        # Initialize analyzers if environment is configured
        try:
            from .market_analyzer import MarketAnalyzer
            self.gpt_analyzer = GPTAnalyzer()
            self.market_analyzer = MarketAnalyzer()
            logging.info("Analyzers initialized successfully")
        except ValueError as e:
            logging.warning(f"Analyzer initialization failed: {e}")
            logging.info("Analysis will proceed without enhancement")
        
    def clone_repository(self) -> str:
        """Clone or copy the repository and return the local path"""
        import tempfile
        import shutil
        
        # Create temp directory for analysis
        self.repo_path = tempfile.mkdtemp(prefix="analysis_")
        
        # If repo_url is a local path, just copy it
        if os.path.exists(self.repo_url):
            logging.info(f"Copying local directory: {self.repo_url}")
            shutil.copytree(self.repo_url, self.repo_path, dirs_exist_ok=True)
        else:
            # Otherwise try to clone from git
            logging.info(f"Cloning repository: {self.repo_url}")
            Repo.clone_from(self.repo_url, self.repo_path)
            
        return self.repo_path
        
    async def analyze(self) -> AnalysisResult:
        """Perform complete analysis of the repository"""
        if not self.repo_path:
            self.clone_repository()
            
        if not self.repo_path:  # Still None after clone attempt
            raise ValueError("Failed to initialize repository path")
            
        repo_path = self.repo_path  # Type narrowing - repo_path is now str
            
        # Initialize sub-analyzers
        from .authenticity_detector import AuthenticityDetector
        from .execution_verifier import ExecutionVerifier
        
        authenticity_detector = AuthenticityDetector(repo_path)
        execution_verifier = ExecutionVerifier(repo_path)
        
        # Perform base analysis
        ai_score = await authenticity_detector.analyze_authenticity()
        exec_score = await execution_verifier.verify_execution()
        
        # Enhance analysis with GPT if available
        if self.gpt_analyzer:
            try:
                # Sample key files for GPT analysis
                sample_files = []
                for root, _, files in os.walk(repo_path):
                    for file in files:
                        if file.endswith(('.py', '.rs', '.ts', '.tsx', '.js', '.jsx')):
                            sample_files.append(os.path.join(root, file))
                
                if sample_files:
                    # Analyze up to rate limit
                    gpt_scores = []
                    for file_path in sample_files[:int(os.getenv('MAX_GPT_CALLS', '5'))]:
                        try:
                            with open(file_path, 'r') as f:
                                code = f.read()
                            
                            # Get GPT analysis
                            result = await self.gpt_analyzer.analyze_code_segment(
                                code,
                                context=f"Analyzing AI implementation in {os.path.basename(file_path)}"
                            )
                            if isinstance(result, dict) and 'ai_score' in result:
                                gpt_scores.append(result['ai_score'])
                            
                        except Exception as e:
                            logging.error(f"GPT analysis failed for {file_path}: {e}")
                            continue
                    
                    # Combine scores if GPT analysis succeeded
                    if gpt_scores:
                        avg_gpt_score = sum(gpt_scores) / len(gpt_scores)
                        # Weight: 70% traditional analysis, 30% GPT analysis
                        ai_score = (ai_score * 0.7) + (avg_gpt_score * 0.3)
                        logging.info(f"Enhanced AI score with GPT analysis: {ai_score:.2f}")
                        
            except Exception as e:
                logging.error(f"GPT enhancement failed: {e}")
                # Continue with original ai_score
        
        # Get market analysis if available
        market_score = 0.5  # Default neutral score
        if self.market_analyzer:
            try:
                project_name = os.path.basename(self.repo_url)
                market_analysis = await self.market_analyzer.analyze_market_value(
                    project_name=project_name,
                    repo_url=self.repo_url
                )
                if isinstance(market_analysis, dict) and 'market_score' in market_analysis:
                    market_score = market_analysis['market_score']
                
                # Add market-based recommendations
                if market_analysis.get('recommendations'):
                    self._market_recommendations = market_analysis['recommendations']
            except Exception as e:
                logging.error(f"Market analysis failed: {e}")

        # Calculate overall scores and collect issues
        logging.info("Creating AnalysisResult with scores: quality=%.2f, ai=%.2f, exec=%.2f, security=%.2f, market=%.2f",
                    self._analyze_code_quality(), ai_score, exec_score, self._analyze_security(), market_score)
        result = AnalysisResult(
            code_quality_score=self._analyze_code_quality(),
            ai_framework_score=ai_score,
            execution_score=exec_score,
            security_score=self._analyze_security(),
            market_value_score=market_score,
            issues=self._collect_issues(),
            recommendations=self._generate_recommendations()
        )
        logging.info("AnalysisResult created successfully, has calculate_overall_score: %s",
                    hasattr(result, 'calculate_overall_score'))
        return result
        
    def _analyze_code_quality(self) -> float:
        """Analyze code quality using static analysis tools"""
        total_score = 0.0
        file_count = 0
        
        if not self.repo_path:
            return 0.0
            
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith(('.py', '.rs', '.ts', '.tsx', '.js', '.jsx')):
                    continue
                    
                file_path = os.path.join(root, file)
                file_count += 1
                
                try:
                    if file.endswith('.py'):
                        score = self._analyze_python_quality(file_path)
                    elif file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                        score = self._analyze_typescript_quality(file_path)
                    else:  # .rs file
                        score = self._analyze_rust_quality(file_path)
                    total_score += score
                except Exception as e:
                    logging.error(f"Error analyzing {file}: {e}")
                    # Return minimum passing score on error
                    total_score += 0.1
                    continue
        
        # Ensure minimum score of 0.1 if any files were analyzed
        return max(0.1, total_score / max(file_count, 1)) if file_count > 0 else 0.0
        
    def _analyze_python_quality(self, file_path: str) -> float:
        """Analyze Python code quality using radon"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        try:
            # Calculate cyclomatic complexity
            blocks = radon_cc.cc_visit(content)
            if blocks:
                complexity_scores = [block.complexity for block in blocks]
                avg_complexity = sum(complexity_scores) / len(complexity_scores)
                complexity_score = max(0, 1 - (avg_complexity / 10))  # Normalize, lower is better
            else:
                complexity_score = 1.0
                
            # Calculate maintainability index
            try:
                mi_result = h_visit(content)
                if isinstance(mi_result, (int, float)):
                    mi_score = float(mi_result)
                else:
                    mi_score = 50.0  # Default score if Halstead metrics fail
                mi_normalized = max(0, min(1, mi_score / 100))  # Convert to 0-1 scale
            except Exception as e:
                logging.warning(f"Failed to calculate maintainability index: {e}")
                mi_normalized = 0.5  # Default to neutral score
            
            # Raw metrics
            raw_metrics = analyze(content)
            loc = raw_metrics.loc
            lloc = raw_metrics.lloc
            comments = raw_metrics.comments
            
            # Calculate documentation ratio
            doc_ratio = comments / max(lloc, 1) if lloc > 0 else 0
            doc_score = min(1, doc_ratio * 2)  # Scale up to reward documentation
            
            # Weighted average of all metrics
            return (complexity_score * 0.4 + mi_normalized * 0.4 + doc_score * 0.2)
        except Exception as e:
            logging.error(f"Error in Python quality analysis: {e}")
            return 0.1  # Return minimum passing score on error
        
    def _analyze_rust_quality(self, file_path: str) -> float:
        """Analyze Rust code quality using basic metrics"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Count lines of code and comments
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = len([l for l in lines if l.strip().startswith('//') or l.strip().startswith('/*')])
        doc_lines = len([l for l in lines if l.strip().startswith('///')])
        
        # Calculate documentation ratio
        doc_ratio = (comment_lines + doc_lines) / max(total_lines, 1)
        doc_score = min(1, doc_ratio * 2)
        
        # Check for proper error handling
        error_handling_patterns = [
            r'Result<.*>',
            r'Option<.*>',
            r'match .*',
            r'\.unwrap_or\(',
            r'\.unwrap_or_else\(',
            r'\.map_err\(',
        ]
        error_handling_score = sum(
            1 for pattern in error_handling_patterns
            if re.search(pattern, content)
        ) / len(error_handling_patterns)
        
        # Check for proper type annotations and documentation
        type_patterns = [
            r'pub struct .*',
            r'pub enum .*',
            r'pub trait .*',
            r'pub fn .*',
            r'impl .*',
        ]
        type_score = sum(
            1 for pattern in type_patterns
            if re.search(pattern, content)
        ) / max(len(type_patterns), 1)
        
        # Weighted average of all metrics
        return (doc_score * 0.3 + error_handling_score * 0.4 + type_score * 0.3)
        
    def _analyze_typescript_quality(self, file_path: str) -> float:
        """Analyze TypeScript/JavaScript code quality"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Count lines of code and comments
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = len([l for l in lines if l.strip().startswith('//') or l.strip().startswith('/*')])
        
        # Calculate documentation ratio
        doc_ratio = comment_lines / max(total_lines, 1)
        doc_score = min(1, doc_ratio * 2)
        
        # Check for proper type annotations (TypeScript)
        type_patterns = [
            r'interface\s+\w+',
            r'type\s+\w+\s*=',
            r':\s*(string|number|boolean|any)\b',
            r'<\w+\s*extends\s*\w+>',
            r'as\s+const',
        ]
        type_score = sum(
            1 for pattern in type_patterns
            if re.search(pattern, content)
        ) / len(type_patterns)
        
        # Check for React/Next.js best practices
        react_patterns = [
            r'export\s+(default\s+)?function\s+\w+',
            r'const\s+\w+\s*=\s*\([^)]*\)\s*:',
            r'useState<',
            r'useEffect',
            r'Props\>',
        ]
        react_score = sum(
            1 for pattern in react_patterns
            if re.search(pattern, content)
        ) / len(react_patterns)
        
        # Check for error handling
        error_patterns = [
            r'try\s*{',
            r'catch\s*\(',
            r'throw\s+new\s+Error',
            r'Promise\.catch',
            r'Error\>',
        ]
        error_score = sum(
            1 for pattern in error_patterns
            if re.search(pattern, content)
        ) / len(error_patterns)
        
        # Weighted average of all metrics
        return (doc_score * 0.2 + type_score * 0.3 + react_score * 0.3 + error_score * 0.2)
        
    def _analyze_security(self) -> float:
        """Analyze security issues"""
        total_score = 0.0
        file_count = 0
        
        if not self.repo_path:
            return 0.0
            
        security_patterns = {
            'api_key_exposure': r'(API_KEY|OPENAI_KEY|SECRET_KEY)\s*=\s*["\'][^"\']+["\']',
            'sql_injection': r'`SELECT.*\$\{',
            'xss_vulnerability': r'dangerouslySetInnerHTML',
            'eval_usage': r'\beval\s*\(',
            'secure_headers': r'helmet\(',
            'csrf_protection': r'csrf',
            'rate_limiting': r'RateLimit|rateLimiter',
            'input_validation': r'zod|yup|joi|validate',
        }
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith(('.py', '.rs', '.ts', '.tsx', '.js', '.jsx')):
                    continue
                    
                file_path = os.path.join(root, file)
                file_count += 1
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for security patterns
                    security_issues = sum(1 for pattern in security_patterns.values()
                                       if not re.search(pattern, content))
                    
                    # Calculate security score (inverse of issues)
                    score = 1 - (security_issues / len(security_patterns))
                    total_score += max(0, score)  # Ensure non-negative
                except Exception as e:
                    print(f"Error analyzing security for {file}: {e}")
                    continue
        
        return total_score / max(file_count, 1)
        
    def _collect_issues(self) -> List[Dict]:
        """Collect all identified issues"""
        return []
        
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        return []
