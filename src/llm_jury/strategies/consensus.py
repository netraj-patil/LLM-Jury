"""
Consensus Strategies.
Implements voting-based aggregation logic (Majority Vote, Consensus Thresholds).
"""

from collections import Counter
from typing import List, Dict, Any
from llm_jury.core.manifest import JudgeScore
from llm_jury.strategies.base import AggregationStrategy, AggregationResult

class MajorityVoting(AggregationStrategy):
    """
    Implements Plurality/Maximum Voting.
    The final score is the one chosen by the most judges.
    """

    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        """
        Determines the winner based on frequency of scores.
        
        Logic:
        1. Round scores to nearest integer (to group similar scores like 4.1 and 3.9).
        2. Count frequencies.
        3. Select the score with the highest count.
        """
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0, metadata={"error": "No scores provided"})

        # Extract numerical scores (rounding to handle minor float variances)
        # We round to 1 decimal place to group "strict" matches, 
        # or integer if strict integer voting is required. 
        # Using rounded integers is safer for "Star Rating" consistency.
        raw_values = [round(s.score) for s in scores]
        
        count_data = Counter(raw_values)
        
        # Get the most common score
        # most_common returns a list of (element, count) tuples
        most_common = count_data.most_common(1)
        
        if not most_common:
             return AggregationResult(score=0.0, confidence=0.0)

        winner_score, winner_count = most_common[0]
        total_votes = len(scores)
        
        # Confidence is the ratio of judges who agreed on the winner
        confidence = winner_count / total_votes if total_votes > 0 else 0.0

        return AggregationResult(
            score=float(winner_score),
            confidence=round(confidence, 4),
            metadata={
                "strategy": "MajorityVoting",
                "vote_distribution": dict(count_data),
                "total_votes": total_votes
            }
        )


class ConsensusStrategy(AggregationStrategy):
    """
    Implements Threshold-based Consensus.
    Requires a specific percentage of judges to agree; otherwise flags low confidence.
    """

    def __init__(self, threshold: float = 0.5):
        """
        Args:
            threshold (float): The minimum agreement ratio required (e.g., 0.5 for >50%).
        """
        self.threshold = threshold

    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        """
        Calculates score and checks if it meets the consensus threshold.
        """
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)

        # Reuse Majority Voting logic to find the candidate
        voter = MajorityVoting()
        result = voter.aggregate(scores)
        
        # Check if the confidence meets the strict threshold
        agreement_ratio = result.confidence
        
        # Metadata update
        result.metadata["strategy"] = "ConsensusStrategy"
        result.metadata["threshold"] = self.threshold
        result.metadata["consensus_reached"] = agreement_ratio >= self.threshold

        # If threshold not met, we still return the score (plurality) 
        # but the caller (JuryEvaluator) can check metadata['consensus_reached']
        # or low confidence to trigger warnings.
        
        return result

    def calculate_agreement(self, scores: List[JudgeScore]) -> float:
        """
        Helper to calculate pure agreement ratio (Inter-judge agreement).
        Useful for diagnostics.
        """
        res = self.aggregate(scores)
        return res.confidence