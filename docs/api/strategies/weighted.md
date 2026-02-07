# Weighted Strategies

Mathematical aggregation implementations that support importance weighting and statistical measures.

## WeightedSum

Assigns different importance levels to each judge.

### Class Definition

```python
class WeightedSum(AggregationStrategy):
    def __init__(self, weights: Dict[str, float])
```

### Constructor

#### Parameters

- **weights** (`Dict[str, float]`): Map of judge IDs to their weights
  - Higher weight = more influence
  - Default weight is 1.0 for judges not in the map

### Formula

```
final_score = Σ(weight_i × score_i) / Σ(weight_i)
```

### Example

```python
from llm_jury.strategies.weighted import WeightedSum
from llm_jury.core.manifest import JudgeScore

# Define trust levels
strategy = WeightedSum(weights={
    "gpt-4o": 2.0,      # Most trusted
    "claude-3": 1.5,    # Trusted
    "gpt-3.5": 1.0,     # Standard
    "llama-3": 0.5      # Less trusted
})

scores = [
    JudgeScore(score=4.5, judge_id="gpt-4o"),
    JudgeScore(score=4.0, judge_id="claude-3"),
    JudgeScore(score=3.5, judge_id="gpt-3.5"),
    JudgeScore(score=3.0, judge_id="llama-3"),
]

result = strategy.aggregate(scores)

# Calculation:
# (2.0 × 4.5) + (1.5 × 4.0) + (1.0 × 3.5) + (0.5 × 3.0)
# --------------------------------------------------------
#              2.0 + 1.5 + 1.0 + 0.5
#
# = 20.5 / 5.0 = 4.1

print(f"Weighted Score: {result.score}")  # 4.1
print(f"Confidence: {result.confidence}")  # 1.0 (all judges in weight map)
```

### Confidence Calculation

Confidence represents how well judges are covered by the weight map:

```python
confidence = judges_with_weights / total_judges
```

#### Examples

```python
# All judges have explicit weights
weights = {"j1": 1.0, "j2": 1.5, "j3": 2.0}
scores = [JudgeScore(judge_id="j1", ...), ...]
# confidence = 3/3 = 1.0

# Some judges missing from weight map
weights = {"j1": 1.0}
scores = [
    JudgeScore(judge_id="j1", ...),  # Has weight
    JudgeScore(judge_id="j2", ...),  # Missing (uses default 1.0)
    JudgeScore(judge_id="j3", ...),  # Missing (uses default 1.0)
]
# confidence = 1/3 = 0.33
```

### Default Weights

Judges not in the weight map default to 1.0:

```python
strategy = WeightedSum(weights={"gpt-4": 2.0})

scores = [
    JudgeScore(score=4.0, judge_id="gpt-4"),     # weight: 2.0
    JudgeScore(score=3.0, judge_id="unknown"),   # weight: 1.0 (default)
]

# (2.0 × 4.0) + (1.0 × 3.0) / (2.0 + 1.0) = 11.0 / 3.0 = 3.67
```

### Determining Weights

#### Based on Validation Accuracy

```python
# Historical accuracy on validation set
validation_results = {
    "gpt-4o": 0.92,      # 92% accuracy
    "claude-3": 0.88,    # 88% accuracy
    "gpt-3.5": 0.75,     # 75% accuracy
}

# Normalize to weights
min_acc = min(validation_results.values())
weights = {
    name: acc / min_acc
    for name, acc in validation_results.items()
}
# weights = {"gpt-4o": 1.23, "claude-3": 1.17, "gpt-3.5": 1.0}
```

#### Based on Cost

```python
# More expensive = higher weight
model_costs = {
    "gpt-4o": 0.05,      # $0.05 per call
    "gpt-3.5": 0.001,    # $0.001 per call
}

# Ratio of costs
weights = {
    "gpt-4o": model_costs["gpt-4o"] / model_costs["gpt-3.5"],
    "gpt-3.5": 1.0
}
# weights = {"gpt-4o": 50.0, "gpt-3.5": 1.0}
```

#### Based on Task Suitability

```python
# Some models better at specific tasks
weights_for_code = {
    "codex": 2.0,
    "gpt-4": 1.5,
    "claude": 1.0
}

weights_for_writing = {
    "claude": 2.0,
    "gpt-4": 1.5,
    "codex": 0.5
}
```

### When to Use

- ✅ Different judge reliability levels
- ✅ Have historical performance data
- ✅ Want fine-grained scores
- ✅ Cost-accuracy trade-offs
- ❌ All judges equally trusted
- ❌ No performance metrics

### Metadata

```python
result.metadata = {
    "strategy": "WeightedSum",
    "total_weight": float,        # Sum of all weights
    "judges_weighted": int        # Judges in weight map
}
```

## WeightedAverage

Simple arithmetic mean with variance-based confidence.

### Class Definition

```python
class WeightedAverage(AggregationStrategy):
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult
```

### Algorithm

1. Calculate arithmetic mean of all scores
2. Calculate variance
3. Derive confidence from variance (low variance = high confidence)

### Formula

```
score = Σ(score_i) / n
variance = Σ((score_i - mean)²) / n
confidence = 1 / (1 + variance)
```

### Example

```python
from llm_jury.strategies.weighted import WeightedAverage

strategy = WeightedAverage()

scores = [
    JudgeScore(score=4.5, judge_id="j1"),
    JudgeScore(score=4.3, judge_id="j2"),
    JudgeScore(score=4.6, judge_id="j3"),
    JudgeScore(score=4.4, judge_id="j4"),
]

result = strategy.aggregate(scores)

# Mean: (4.5 + 4.3 + 4.6 + 4.4) / 4 = 4.45
# Variance: ((0.05² + 0.15² + 0.15² + 0.05²) / 4 = 0.0125
# Confidence: 1 / (1 + 0.0125) = 0.987

print(f"Average Score: {result.score}")  # 4.45
print(f"Confidence: {result.confidence}")  # 0.987 (very high - low variance)
```

### High Agreement Example

```python
# All judges agree closely
scores = [
    JudgeScore(score=4.0, judge_id="j1"),
    JudgeScore(score=4.0, judge_id="j2"),
    JudgeScore(score=4.0, judge_id="j3"),
]

result = strategy.aggregate(scores)
# Mean: 4.0
# Variance: 0.0
# Confidence: 1.0 (perfect agreement)
```

### Low Agreement Example

```python
# Judges strongly disagree
scores = [
    JudgeScore(score=5.0, judge_id="j1"),
    JudgeScore(score=2.0, judge_id="j2"),
    JudgeScore(score=4.0, judge_id="j3"),
    JudgeScore(score=3.0, judge_id="j4"),
]

result = strategy.aggregate(scores)
# Mean: 3.5
# Variance: 1.25
# Confidence: 0.44 (low - high variance)
```

### Confidence Interpretation

```python
result = strategy.aggregate(scores)

if result.confidence > 0.9:
    print("Very high agreement")
elif result.confidence > 0.7:
    print("Good agreement")
elif result.confidence > 0.5:
    print("Moderate agreement")
else:
    print("Low agreement - review needed")
```

### When to Use

- ✅ All judges equally trusted
- ✅ Want continuous scores
- ✅ Need statistical measures
- ✅ Standard evaluation scenarios
- ❌ Need discrete scores
- ❌ Different judge weights

### Metadata

```python
result.metadata = {
    "strategy": "WeightedAverage",
    "variance": float  # Score variance
}
```

## Comparison

| Aspect | WeightedSum | WeightedAverage |
|--------|-------------|-----------------|
| **Equal Weights** | Optional (explicit map) | Always equal |
| **Confidence Basis** | Coverage in weight map | Variance |
| **Use Case** | Unequal judge quality | Standard averaging |
| **Configuration** | Requires weights dict | No configuration |
| **Complexity** | Higher | Lower |

## Best Practices

### For WeightedSum

1. **Base weights on data** (validation accuracy, not intuition)
2. **Include all judges** in weight map for full confidence
3. **Update weights** as judge performance evolves
4. **Document rationale** for chosen weights
5. **Test sensitivity** to weight changes

### For WeightedAverage

1. **Use with 3+ judges** for meaningful variance
2. **Monitor confidence** to detect disagreements
3. **Combine with threshold** for quality gates
4. **Good default** when no weight data available
5. **Interpret variance** to understand judge alignment

## Testing

```python
from llm_jury.core.manifest import JudgeScore

# Test weighted sum
def test_weighted_sum():
    strategy = WeightedSum(weights={"j1": 2.0, "j2": 1.0})
    
    scores = [
        JudgeScore(score=4.0, judge_id="j1"),
        JudgeScore(score=2.0, judge_id="j2"),
    ]
    
    result = strategy.aggregate(scores)
    # (2.0 × 4.0 + 1.0 × 2.0) / 3.0 = 10.0 / 3.0 = 3.33
    assert abs(result.score - 3.33) < 0.01
    assert result.confidence == 1.0  # Both in weight map

# Test weighted average
def test_weighted_average():
    strategy = WeightedAverage()
    
    # Perfect agreement
    scores = [JudgeScore(score=4.0, judge_id=f"j{i}") for i in range(3)]
    result = strategy.aggregate(scores)
    assert result.score == 4.0
    assert result.confidence == 1.0  # Zero variance
    
    # High variance
    scores = [
        JudgeScore(score=1.0, judge_id="j1"),
        JudgeScore(score=5.0, judge_id="j2"),
    ]
    result = strategy.aggregate(scores)
    assert result.score == 3.0
    assert result.confidence < 0.5  # High variance
```

## Advanced: Combining Strategies

```python
class HybridStrategy(AggregationStrategy):
    def __init__(self, weights):
        self.weighted = WeightedSum(weights)
        self.average = WeightedAverage()
    
    def aggregate(self, scores):
        # Get both results
        weighted_result = self.weighted.aggregate(scores)
        average_result = self.average.aggregate(scores)
        
        # Use variance to decide which to trust
        if average_result.confidence > 0.8:
            # High agreement - use simple average
            return average_result
        else:
            # Disagreement - use weighted approach
            return weighted_result
```

## See Also

- [AggregationStrategy (Base)](base.md)
- [Consensus Strategies](consensus.md)
- [JuryEvaluator](../core/evaluator.md)
