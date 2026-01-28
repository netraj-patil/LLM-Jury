"""
Core Manifest and Result Structures.
Defines the data objects for capturing judge scores, evaluation manifests, and final results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class JudgeScore:
    """
    Represents a single evaluation from a single judge.
    
    Attributes:
        score (float): The primary numerical result (normalized or raw depending on context).
        reasoning (str): The textual justification provided by the judge.
        judge_id (str): The identifier of the judge (e.g., 'gpt-4o', 'human-evaluator').
        metrics_metadata (Dict[str, float]): A map holding sub-metrics if the judge
                                             evaluated multiple dimensions at once.
    """
    score: float = 0.0
    reasoning: str = ""
    judge_id: str = "unknown"
    metrics_metadata: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the score to a dictionary."""
        return {
            "score": self.score,
            "reasoning": self.reasoning,
            "judge_id": self.judge_id,
            "metrics_metadata": self.metrics_metadata
        }


@dataclass
class JuryManifest:
    """
    A comprehensive audit trail for a specific evaluation event.
    
    Attributes:
        individual_scores (List[JudgeScore]): The list of raw scores from all judges.
        features (Dict[str, Any]): Textual features extracted during evaluation (e.g., word count).
        metadata (Dict[str, Any]): Additional context (latency, model params, etc.).
        timestamp (datetime): When the evaluation occurred.
    """
    individual_scores: List[JudgeScore] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the manifest for logging/storage."""
        return {
            "individual_scores": [s.to_dict() for s in self.individual_scores],
            "features": self.features,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EvaluationResult:
    """
    The final aggregated result of an evaluation process.
    
    Attributes:
        final_score (float): The aggregated score (e.g., average, weighted sum, consensus).
        is_valid (bool): Whether the result passed the threshold for validity.
        confidence (float): A score representing the inter-judge agreement or certainty.
        manifest (JuryManifest): The detailed audit trail of how this result was reached.
    """
    final_score: float = 0.0
    is_valid: bool = False
    confidence: float = 0.0
    manifest: JuryManifest = field(default_factory=JuryManifest)

    def get_recommendation(self) -> str:
        """
        Returns a high-level recommendation based on the score and validity.
        Implementation of Class Diagram method: getRecommendation().
        """
        if not self.is_valid:
            return "REJECT: The content failed to meet the evaluation threshold."
        
        if self.confidence < 0.5:
            return "WARNING: Passed threshold, but jury agreement is low."
            
        return "APPROVE: The content meets quality standards with high confidence."


@dataclass
class BatchEvaluationResult:
    """
    Container for results when evaluating multiple items or multiple metrics at once.
    
    Attributes:
        results (Dict[str, EvaluationResult]): Map of IDs (or Metric names) to their results.
    """
    results: Dict[str, EvaluationResult] = field(default_factory=dict)

    def get_score(self, metric_name: str) -> float:
        """Retrieve the score for a specific metric name."""
        if metric_name in self.results:
            return self.results[metric_name].final_score
        return 0.0

    def overall_quality(self) -> float:
        """Calculates a simple average of all valid results in the batch."""
        if not self.results:
            return 0.0
        
        total = sum(r.final_score for r in self.results.values())
        return total / len(self.results)

    def get_manifest(self) -> Dict[str, Any]:
        """Aggregates all manifests into a single dictionary view."""
        return {k: v.manifest.to_dict() for k, v in self.results.items()}