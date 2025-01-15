from typing import Dict, List
from dataclasses import dataclass
from .code_analyzer import AnalysisResult

@dataclass
class Report:
    overall_score: float
    detailed_scores: Dict[str, float]
    issues: List[Dict]
    recommendations: List[str]

class ReportGenerator:
    """Generates analysis reports in various formats"""
    
    def __init__(self, analysis_result: AnalysisResult):
        self.result = analysis_result
        
    def generate_summary(self) -> Report:
        """Generate a summary report with market value metrics"""
        # Get valid base scores (non-zero)
        base_scores = [
            score for score in [
                self.result.ai_framework_score,
                self.result.code_quality_score,
                self.result.execution_score,
                self.result.security_score
            ] if score > 0
        ]
        
        # Calculate market contribution (always exactly 30%)
        market_contribution = self.result.market_value_score * 0.3
        score_override = False
        
        # Calculate base score (up to 70%)
        if base_scores:
            # First normalize base scores to 0-1 range
            normalized_base = sum(base_scores) / len(base_scores)
            # Then apply 70% weight
            base_score = normalized_base * 0.7
            
            # For high market success (>= 0.8), ensure minimum total score of 0.5
            # but only if we have valid base scores
            if self.result.market_value_score >= 0.8:
                # Calculate minimum required base score
                min_base = 0.5 - market_contribution
                base_score = max(base_score, min_base)
                score_override = True
        else:
            # When no base scores, only use market contribution
            base_score = 0.0
        
        # Calculate total score (market value always contributes exactly 30%)
        overall_score = base_score + market_contribution
        
        # Prepare detailed scores with exact values from analysis
        detailed_scores = {
            'AI Framework Integration': self.result.ai_framework_score,
            'Code Quality': self.result.code_quality_score,
            'Execution Performance': self.result.execution_score,
            'Market Success': self.result.market_value_score,  # Use exact market value score
            'Code Originality': self.result.security_score  # Using security score for originality
        }
        
        # Add override notification if applied
        recommendations = list(self.result.recommendations)
        if score_override:
            recommendations.insert(0, 
                "NOTE: Project score was adjusted to minimum 5.0/10 due to high market success")
        
        return Report(
            overall_score=overall_score,
            detailed_scores=detailed_scores,
            issues=self.result.issues,
            recommendations=recommendations
        )
        
    def _calculate_overall_score(self) -> float:
        """Calculate the overall project score with equal weights"""
        weights = {
            'ai_framework': 0.25,  # AI Implementation Authenticity
            'code_quality': 0.25,  # Code Feasibility
            'execution': 0.25,     # Execution Performance
            'security': 0.25       # Code Originality
        }
        
        # Calculate base score without market value
        base_score = (
            weights['ai_framework'] * self.result.ai_framework_score +
            weights['code_quality'] * self.result.code_quality_score +
            weights['execution'] * self.result.execution_score +
            weights['security'] * self.result.security_score
        )
        
        # Apply market value boost for popular projects
        if self.result.market_value_score >= 0.8:
            # Ensure minimum 5.0/10 score for popular projects
            base_score = max(base_score, 0.5)
            
        return base_score
