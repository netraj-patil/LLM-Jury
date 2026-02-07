# AggregationStrategy (Base)

Abstract base class for combining multiple judge scores into a single verdict.

## Classes

### AggregationResult

Data class representing the output of aggregation.

```python
@dataclass
class AggregationResult:
    score: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Attributes

- **score** (`float`): The final calculated score after aggregation
- **confidence** (`float`): Measure of agreement or certainty (0.0-1.0)
- **metadata** (`Dict[str, Any]`): Additional details about the calculation

#### Example

```python
result = AggregationResult(
    score=4.2,
    confidence=0.85,
    metadata={
        "strategy": "WeightedSum",
        "total_weight": 3.5,
        "judges_weighted": 3
    }
)
```

### AggregationStrategy

Abstract base class for aggregation logic.

```python
from abc import ABC, abstractmethod

class AggregationStrategy(ABC):
    @abstractmethod
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult
```

## Abstract Method

### aggregate

```python
@abstractmethod
def aggregate(self, scores: List[JudgeScore]) -> AggregationResult
```

Combines a list of individual judge scores into a single result.

#### Parameters

- **scores** (`List[JudgeScore]`): Raw scores from all judges

#### Returns

`AggregationResult`: Final score, confidence, and metadata

#### Example Implementation

```python
class SimpleAverage(AggregationStrategy):
    def aggregate(self, scores):
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        # Calculate average
        total = sum(s.score for s in scores)
        avg = total / len(scores)
        
        # Confidence based on agreement
        variance = sum((s.score - avg) ** 2 for s in scores) / len(scores)
        confidence = 1.0 / (1.0 + variance)
        
        return AggregationResult(
            score=avg,
            confidence=confidence,
            metadata={"strategy": "SimpleAverage", "variance": variance}
        )
```

## Implementing Custom Strategies

### Median Strategy

```python
class MedianStrategy(AggregationStrategy):
    def aggregate(self, scores):
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        values = sorted([s.score for s in scores])
        n = len(values)
        
        # Calculate median
        if n % 2 == 0:
            median = (values[n//2 - 1] + values[n//2]) / 2
        else:
            median = values[n//2]
        
        # Confidence from IQR (interquartile range)
        if n >= 4:
            q1 = values[n//4]
            q3 = values[3*n//4]
            iqr = q3 - q1
            confidence = 1.0 / (1.0 + iqr)
        else:
            confidence = 0.5
        
        return AggregationResult(
            score=median,
            confidence=confidence,
            metadata={"strategy": "Median"}
        )
```

### Threshold-Based Strategy

```python
class ThresholdStrategy(AggregationStrategy):
    def __init__(self, threshold=0.8):
        self.threshold = threshold
    
    def aggregate(self, scores):
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        # Calculate average
        avg = sum(s.score for s in scores) / len(scores)
        
        # Count how many are above threshold
        above_threshold = sum(1 for s in scores if s.score >= self.threshold * 5.0)
        agreement = above_threshold / len(scores)
        
        return AggregationResult(
            score=avg,
            confidence=agreement,
            metadata={
                "strategy": "Threshold",
                "threshold": self.threshold,
                "above_threshold": above_threshold
            }
        )
```

### Judge Confidence Weighting

```python
class ConfidenceWeightedStrategy(AggregationStrategy):
    def aggregate(self, scores):
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        # Weight by judge confidence (from metadata if available)
        weighted_sum = 0.0
        total_confidence = 0.0
        
        for score in scores:
            # Assume confidence is in metadata
            judge_confidence = score.metrics_metadata.get("confidence", 1.0)
            weighted_sum += score.score * judge_confidence
            total_confidence += judge_confidence
        
        final_score = weighted_sum / total_confidence if total_confidence > 0 else 0.0
        
        # Overall confidence is average of judge confidences
        avg_confidence = total_confidence / len(scores) if scores else 0.0
        
        return AggregationResult(
            score=final_score,
            confidence=avg_confidence,
            metadata={"strategy": "ConfidenceWeighted"}
        )
```

### Outlier-Resistant Strategy

```python
class TrimmedMeanStrategy(AggregationStrategy):
    def __init__(self, trim_fraction=0.2):
        """
        Args:
            trim_fraction: Fraction of scores to remove from each end (e.g., 0.2 = remove 20%)
        """
        self.trim_fraction = trim_fraction
    
    def aggregate(self, scores):
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        values = sorted([s.score for s in scores])
        n = len(values)
        
        # Calculate how many to trim
        trim_count = int(n * self.trim_fraction)
        
        if trim_count == 0:
            # Not enough scores to trim
            trimmed = values
        else:
            # Remove highest and lowest
            trimmed = values[trim_count:-trim_count]
        
        # Calculate mean of remaining
        avg = sum(trimmed) / len(trimmed) if trimmed else 0.0
        
        # Confidence: what fraction remained
        confidence = len(trimmed) / n if n > 0 else 0.0
        
        return AggregationResult(
            score=avg,
            confidence=confidence,
            metadata={
                "strategy": "TrimmedMean",
                "trim_fraction": self.trim_fraction,
                "scores_used": len(trimmed)
            }
        )
```

## Confidence Calculation

Different approaches for calculating confidence:

### Variance-Based

```python
# Low variance = high agreement = high confidence
variance = sum((s.score - mean) ** 2 for s in scores) / len(scores)
confidence = 1.0 / (1.0 + variance)
```

### Agreement Ratio

```python
# Fraction of judges agreeing with winner
winner_count = max(Counter(scores).values())
confidence = winner_count / len(scores)
```

### Range-Based

```python
# Smaller range = higher confidence
score_range = max(scores) - min(scores)
confidence = 1.0 / (1.0 + score_range)
```

### IQR-Based

```python
# Interquartile range - resistant to outliers
q1, q3 = percentile(scores, [25, 75])
iqr = q3 - q1
confidence = 1.0 / (1.0 + iqr)
```

## Best Practices

1. **Handle empty scores**: Always check `if not scores`
2. **Return 0 confidence** for failures or edge cases
3. **Include metadata**: Help users understand the decision
4. **Consistent confidence**: Use 0.0-1.0 range
5. **Document behavior**: Explain edge cases
6. **Test thoroughly**: Verify with various score patterns

## Testing Custom Strategies

```python
from llm_jury.core.manifest import JudgeScore

# Create test scores
test_scores = [
    JudgeScore(score=4.0, reasoning="Good", judge_id="judge1"),
    JudgeScore(score=4.2, reasoning="Very good", judge_id="judge2"),
    JudgeScore(score=3.8, reasoning="Good", judge_id="judge3"),
]

# Test your strategy
strategy = CustomStrategy()
result = strategy.aggregate(test_scores)

print(f"Score: {result.score}")
print(f"Confidence: {result.confidence}")
print(f"Metadata: {result.metadata}")

# Test edge cases
empty_result = strategy.aggregate([])
assert empty_result.score == 0.0
assert empty_result.confidence == 0.0
```

## See Also

- [Consensus Strategies](consensus.md)
- [Weighted Strategies](weighted.md)
- [JudgeScore](../core/manifest.md#judgescore)
- [JuryEvaluator](../core/evaluator.md)
