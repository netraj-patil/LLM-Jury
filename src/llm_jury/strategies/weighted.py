"""
Weighted Aggregation Strategies.
Implements math-based aggregation logic (Weighted Sum, Average) for reliability scoring.
"""

from typing import List, Dict
from llm_jury.core.manifest import JudgeScore
from llm_jury.strategies.base import AggregationStrategy, AggregationResult

class WeightedSum(AggregationStrategy):
    """
    Implements a Weighted Sum strategy where specific judges have higher influence.
    Useful when you trust some models (e.g., GPT-4) more than others (e.g., Llama-2).
    
    Formula: S = sum(w_i * score_i) / sum(w_i)
    """

    def __init__(self, weights: Dict[str, float]):
        """
        Args:
            weights (Dict[str, float]): Map of judge_id (or name) to their weight.
                                      e.g., {"gpt-4": 1.0, "llama-2": 0.5}
        """
        self.weights = weights

    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        """
        Calculates the weighted average of the scores.
        """
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)

        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Track which judges were found vs missing in the weight map
        found_judges = 0

        for score_obj in scores:
            # Default weight is 1.0 if not specified in the map
            # We use judge_id (defined in Manifest) to lookup weight
            judge_id = score_obj.judge_id
            weight = self.weights.get(judge_id, 1.0)
            
            total_weighted_score += score_obj.score * weight
            total_weight += weight
            
            if judge_id in self.weights:
                found_judges += 1

        final_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Confidence: How much of the jury did we actually have specific weights for?
        # If we have weights for all judges, confidence is high (1.0).
        confidence = found_judges / len(scores) if scores else 0.0

        return AggregationResult(
            score=final_score,
            confidence=confidence,
            metadata={
                "strategy": "WeightedSum",
                "total_weight": total_weight,
                "judges_weighted": found_judges
            }
        )


class WeightedAverage(AggregationStrategy):
    """
    Implements a simple Arithmetic Mean (Average).
    Treats all judges equally.
    """

    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        """
        Calculates the simple average of all scores.
        """
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)

        # Simple sum divided by count
        total_score = sum(s.score for s in scores)
        count = len(scores)
        
        average = total_score / count

        # Standard deviation could be a good confidence metric here (low std dev = high confidence)
        # For simplicity, we calculate Variance roughly to hint at disagreement.
        variance = sum((s.score - average) ** 2 for s in scores) / count
        # Inverse variance as confidence (higher variance = lower confidence)
        # Normalized roughly: 1.0 / (1.0 + variance)
        confidence = 1.0 / (1.0 + variance)

        return AggregationResult(
            score=average,
            confidence=round(confidence, 4),
            metadata={
                "strategy": "WeightedAverage",
                "variance": round(variance, 4)
            }
        )