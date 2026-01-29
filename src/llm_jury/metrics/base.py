"""
Base Metric Interface.
Defines the abstract contract for evaluation criteria, prompt generation, and score normalization.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Metric(ABC):
    """
    Abstract base class for all evaluation metrics.
    
    A Metric defines *what* is being measured (Name/Description), *how* to ask the judge 
    (Prompt), and *how* to standardize the resulting score (Normalization).

    Attributes:
        name (str): The unique identifier for this metric (e.g., "Groundedness").
        description (str): A brief explanation of the metric for documentation/metadata.
        scale_min (float): The minimum possible raw score (default 1.0).
        scale_max (float): The maximum possible raw score (default 5.0).
    """

    def __init__(
        self, 
        name: str, 
        description: str, 
        scale_min: float = 1.0, 
        scale_max: float = 5.0
    ):
        """
        Initialize the metric with definition and scoring scale.
        
        Args:
            name (str): Metric identifier.
            description (str): Human-readable description.
            scale_min (float): Lower bound of the scoring range (e.g., 1).
            scale_max (float): Upper bound of the scoring range (e.g., 5 or 10).
        """
        self.name = name
        self.description = description
        self.scale_min = scale_min
        self.scale_max = scale_max
    
    @abstractmethod
    def get_prompt(self, context: Any = None) -> str:
        """
        Returns the specific evaluation instruction (prompt) for this metric.
        
        Subclasses must implement this to return the text that tells the Judge 
        exactly what to look for (e.g., "Is the answer supported by the context?").

        Args:
            context (Any): Optional context data that might need to be injected 
                           dynamically into the prompt string.

        Returns:
            str: The fully formed prompt string to be passed to the Judge.
        """
        pass

    def normalize(self, score: float) -> float:
        """
        Normalizes a raw score into a unified [0, 1] range.

        Formula: (x - min) / (max - min)

        Args:
            score (float): The raw score returned by a judge.

        Returns:
            float: A value between 0.0 and 1.0.
        """
        if self.scale_max == self.scale_min:
            return 0.0 # Avoid division by zero
        
        # Clamp score to range before normalizing
        clamped_score = max(self.scale_min, min(score, self.scale_max))
        
        return (clamped_score - self.scale_min) / (self.scale_max - self.scale_min)
    
    def aggregate_metrics(self, metric_scores: Dict[str, float]) -> float:
       """
       Optional: Aggregates multiple metric scores into a single value.
       Default implementation returns the average.
       """
       if not metric_scores:
           return 0.0
       return sum(metric_scores.values()) / len(metric_scores)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', scale=[{self.scale_min}, {self.scale_max}])>"