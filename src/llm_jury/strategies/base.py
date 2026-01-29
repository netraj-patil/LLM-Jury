"""
Aggregation Strategy Interface.
Defines the contract for combining multiple judge scores into a single verdict.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm_jury.core.manifest import JudgeScore

@dataclass
class AggregationResult:
    """
    The result of an aggregation process.
    
    Attributes:
        score (float): The final calculated score.
        confidence (float): A measure of agreement or certainty (0.0 to 1.0).
        metadata (Dict): details about the calculation (e.g., vote counts).
    """
    score: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class AggregationStrategy(ABC):
    """
    Abstract base class for aggregation logic.
    """

    @abstractmethod
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        """
        Combines a list of individual JudgeScores into a single result.
        
        Args:
            scores (List[JudgeScore]): The raw scores from the jury.
            
        Returns:
            AggregationResult: The final score and confidence metrics.
        """
        pass