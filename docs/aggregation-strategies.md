# Aggregation Strategies

How to combine multiple judge scores into a single reliable verdict.

## Table of Contents

- [Why Aggregation Matters](#why-aggregation-matters)
- [Available Strategies](#available-strategies)
- [Choosing a Strategy](#choosing-a-strategy)
- [Strategy Comparison](#strategy-comparison)
- [Advanced Usage](#advanced-usage)
- [Custom Strategies](#custom-strategies)

---

## Why Aggregation Matters

When multiple judges evaluate the same content, they may disagree. Aggregation strategies resolve these disagreements systematically.

**Example Scenario**:
```
Judge 1 (GPT-4):     Score = 4
Judge 2 (Claude):    Score = 5
Judge 3 (Gemini):    Score = 4
```

How do we get a final score? Different strategies give different results.

---

## Available Strategies

### 1. MajorityVoting

**Principle**: The most common score wins (plurality).

**Location**: `llm_jury.strategies.consensus.MajorityVoting`

**Usage**:
```python
from llm_jury.strategies.consensus import MajorityVoting

strategy = MajorityVoting()
jury = JuryEvaluator(judges=[...], strategy=strategy)
```

**How It Works**:
1. Rounds scores to nearest integer
2. Counts frequency of each score
3. Returns the most frequent score
4. Confidence = (votes for winner) / (total votes)

**Example**:
```python
# Input scores: [4, 4, 3, 4, 5]
# Vote counts: {4: 3, 3: 1, 5: 1}
# Winner: 4 (3 out of 5 judges)
# Result: score=4.0, confidence=0.6
```

**Best For**:
- Democratic consensus
- When all judges are equally trusted
- Discrete score scales (1-5, not 0.0-1.0)

**Pros**:
- Simple and intuitive
- Clear winner in most cases
- High confidence when agreement is strong

**Cons**:
- Loses information (doesn't use score magnitude)
- Can be unstable with small panels
- Requires rounding (loses precision)

---

### 2. ConsensusStrategy

**Principle**: Requires minimum agreement threshold to be confident.

**Location**: `llm_jury.strategies.consensus.ConsensusStrategy`

**Usage**:
```python
from llm_jury.strategies.consensus import ConsensusStrategy

strategy = ConsensusStrategy(threshold=0.6)  # Require 60% agreement
jury = JuryEvaluator(judges=[...], strategy=strategy)
```

**Parameters**:
- `threshold` (float): Minimum agreement ratio (0.0 to 1.0)

**How It Works**:
1. Uses MajorityVoting to find winner
2. Checks if agreement ratio meets threshold
3. Flags `consensus_reached` in metadata

**Example**:
```python
# Scores: [4, 4, 3, 4, 5]
# Winner: 4 with 60% agreement
# Threshold: 0.6

strategy = ConsensusStrategy(threshold=0.6)
result = strategy.aggregate(scores)
# Returns: score=4.0, confidence=0.6
# Metadata: consensus_reached=True (0.6 >= 0.6)

# With higher threshold
strategy = ConsensusStrategy(threshold=0.8)
result = strategy.aggregate(scores)
# Returns: score=4.0, confidence=0.6
# Metadata: consensus_reached=False (0.6 < 0.8)
```

**Best For**:
- High-stakes decisions requiring strong agreement
- Compliance checks where uncertainty is risky
- Quality control with strict standards

**Pros**:
- Explicit confidence requirements
- Flags low-agreement cases
- Built-in quality control

**Cons**:
- May reject valid results if threshold too high
- Still uses plurality (loses precision)

**Recommended Thresholds**:
- `0.5` (50%): Basic majority
- `0.6-0.7`: Moderate confidence
- `0.8+`: High confidence (strict)

---

### 3. WeightedSum

**Principle**: Some judges have more influence (weighted average).

**Location**: `llm_jury.strategies.weighted.WeightedSum`

**Usage**:
```python
from llm_jury.strategies.weighted import WeightedSum

strategy = WeightedSum(weights={
    "gpt-4": 1.0,
    "gpt-3.5": 0.5,
    "llama-2": 0.3
})
jury = JuryEvaluator(judges=[...], strategy=strategy)
```

**Parameters**:
- `weights` (Dict[str, float]): Map of judge_id to weight

**How It Works**:
1. Multiplies each score by its judge's weight
2. Sums all weighted scores
3. Divides by sum of weights
4. Confidence = ratio of judges with explicit weights

**Formula**: `final_score = Σ(weight_i × score_i) / Σ(weight_i)`

**Example**:
```python
# Judges and scores:
# gpt-4 (weight 1.0): score 4.5
# gpt-3.5 (weight 0.5): score 3.0
# llama-2 (weight 0.3): score 3.5

# Calculation:
# (1.0 × 4.5 + 0.5 × 3.0 + 0.3 × 3.5) / (1.0 + 0.5 + 0.3)
# = (4.5 + 1.5 + 1.05) / 1.8
# = 7.05 / 1.8
# = 3.92

# Result: score=3.92, confidence=1.0 (all have weights)
```

**Default Weight**: Judges without explicit weights get 1.0

**Best For**:
- When some models are more reliable for your domain
- Trained classifier weights from A/B testing
- Cost-quality tradeoffs (strong model + fast models)

**Pros**:
- Leverages model strengths
- Flexible (can adjust weights easily)
- Preserves precision (no rounding)

**Cons**:
- Requires knowing which judges to trust
- Can overweight one judge
- Needs calibration for your domain

**Weight Selection Tips**:

1. **Equal Baseline**: Start with all weights = 1.0
2. **Quality-Based**: Higher weights for better models
   ```python
   weights = {
       "gpt-4": 1.0,        # State-of-the-art
       "gpt-3.5": 0.7,      # Good but less capable
       "llama-2-7b": 0.3    # Fast but less accurate
   }
   ```
3. **Cost-Aware**: Balance quality and cost
   ```python
   # 1 expensive + 2 cheap models
   weights = {
       "gpt-4": 0.6,        # High quality
       "gpt-3.5-1": 0.2,    # Budget
       "gpt-3.5-2": 0.2     # Budget
   }
   ```
4. **Empirical**: Measure correlation with ground truth
   ```python
   # Run evaluation, compare to human labels
   # Adjust weights based on per-model accuracy
   ```

---

### 4. WeightedAverage

**Principle**: Simple arithmetic mean (all judges equal).

**Location**: `llm_jury.strategies.weighted.WeightedAverage`

**Usage**:
```python
from llm_jury.strategies.weighted import WeightedAverage

strategy = WeightedAverage()
jury = JuryEvaluator(judges=[...], strategy=strategy)
```

**How It Works**:
1. Sums all scores
2. Divides by count
3. Confidence = `1.0 / (1.0 + variance)`

**Formula**: `final_score = Σ(score_i) / n`

**Example**:
```python
# Scores: [4.5, 3.8, 4.2, 4.0]
# Average: (4.5 + 3.8 + 4.2 + 4.0) / 4 = 4.125
# Variance: 0.0625
# Confidence: 1.0 / (1.0 + 0.0625) = 0.941

# Result: score=4.125, confidence=0.941
```

**Best For**:
- Quick prototyping
- When all models are comparable
- Continuous score scales (normalized 0-1)

**Pros**:
- Simplest approach
- Preserves precision
- No configuration needed

**Cons**:
- Treats all judges equally (may not be appropriate)
- Influenced by outliers
- Low confidence with high variance

**Confidence Interpretation**:
- High confidence (>0.9): Low variance, judges agree
- Medium confidence (0.5-0.9): Some disagreement
- Low confidence (<0.5): High variance, judges disagree

---

## Choosing a Strategy

### Decision Tree

```
Do you have explicit judge weights (trained, calibrated)?
├─ Yes → WeightedSum
└─ No
   └─ Do you need strict agreement thresholds?
      ├─ Yes → ConsensusStrategy
      └─ No
         └─ Do you prefer discrete votes or continuous averaging?
            ├─ Discrete → MajorityVoting
            └─ Continuous → WeightedAverage
```

### By Use Case

| Use Case | Recommended Strategy | Reason |
|----------|---------------------|---------|
| RAG Evaluation | MajorityVoting | Clear consensus on groundedness |
| Compliance Check | ConsensusStrategy (0.8+) | Need high confidence |
| Content Moderation | WeightedSum | Trust safety-focused models more |
| Quick Prototyping | WeightedAverage | Simple, no configuration |
| Production System | WeightedSum (calibrated) | Optimize for your domain |
| Cost Optimization | WeightedSum | Balance quality vs price |

### By Judge Count

| Judges | Recommended Strategy | Notes |
|--------|---------------------|-------|
| 1 | N/A | No aggregation needed |
| 2 | WeightedAverage | Avoid ties |
| 3-5 | MajorityVoting | Sweet spot for voting |
| 5-7 | ConsensusStrategy | Enough for strong consensus |
| 7+ | WeightedAverage | Reduces impact of outliers |

---

## Strategy Comparison

### Same Scores, Different Strategies

Given scores: `[4.2, 3.8, 4.5, 4.0, 3.9]`

```python
# MajorityVoting (rounds to integers)
# Rounded: [4, 4, 5, 4, 4]
# Result: score=4.0, confidence=0.8 (4 out of 5)

# ConsensusStrategy (threshold=0.6)
# Result: score=4.0, confidence=0.8, consensus_reached=True

# WeightedSum (gpt-4=1.0, others=0.5)
# Assuming first judge is gpt-4
# Result: score ≈ 4.1, confidence=0.2 (only 1 judge weighted)

# WeightedAverage
# Result: score=4.08, confidence=0.964 (low variance)
```

**Key Differences**:
- **MajorityVoting**: Loses precision (4.08 → 4.0)
- **ConsensusStrategy**: Same as majority + threshold check
- **WeightedSum**: Can favor specific judges
- **WeightedAverage**: Preserves precision, penalizes variance

---

## Advanced Usage

### Dynamic Strategy Selection

Choose strategy based on context:

```python
def get_strategy(use_case: str):
    if use_case == "compliance":
        return ConsensusStrategy(threshold=0.8)
    elif use_case == "production":
        return WeightedSum({"gpt-4": 1.0, "gpt-3.5": 0.6})
    else:
        return MajorityVoting()

strategy = get_strategy("compliance")
jury = JuryEvaluator(judges=[...], strategy=strategy)
```

### Switching Strategies Mid-Flight

```python
jury = JuryEvaluator(judges=[...])

# Start with simple averaging
jury.set_strategy(WeightedAverage())
result1 = jury.evaluate(...)

# Switch to weighted for production
jury.set_strategy(WeightedSum({"gpt-4": 1.0, "gpt-3.5": 0.5}))
result2 = jury.evaluate(...)
```

### Analyzing Disagreement

```python
result = jury.evaluate(...)

# Check individual scores
scores = [s.score for s in result.manifest.individual_scores]
print(f"Score range: {min(scores)} - {max(scores)}")
print(f"Confidence: {result.confidence}")

# Log if low confidence
if result.confidence < 0.6:
    print("WARNING: Low judge agreement")
    for score_obj in result.manifest.individual_scores:
        print(f"  {score_obj.judge_id}: {score_obj.score} - {score_obj.reasoning[:100]}")
```

### Ensemble of Strategies

Run multiple strategies and compare:

```python
strategies = [
    MajorityVoting(),
    WeightedAverage(),
    ConsensusStrategy(threshold=0.7)
]

for strategy in strategies:
    jury.set_strategy(strategy)
    result = jury.evaluate(...)
    print(f"{strategy.__class__.__name__}: {result.final_score:.2f} (conf: {result.confidence:.2f})")
```

---

## Custom Strategies

Create your own aggregation logic:

```python
from llm_jury.strategies.base import AggregationStrategy, AggregationResult
from typing import List
from llm_jury.core.manifest import JudgeScore

class MedianStrategy(AggregationStrategy):
    """
    Uses the median score instead of mean or mode.
    More robust to outliers than average.
    """
    
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        if not scores:
            return AggregationResult(score=0.0, confidence=0.0)
        
        # Extract and sort scores
        values = sorted([s.score for s in scores])
        n = len(values)
        
        # Calculate median
        if n % 2 == 0:
            median = (values[n//2 - 1] + values[n//2]) / 2
        else:
            median = values[n//2]
        
        # Confidence: Use IQR (interquartile range)
        # Lower IQR = higher confidence
        q1 = values[n//4]
        q3 = values[3*n//4]
        iqr = q3 - q1
        confidence = 1.0 / (1.0 + iqr)
        
        return AggregationResult(
            score=median,
            confidence=confidence,
            metadata={
                "strategy": "MedianStrategy",
                "iqr": iqr,
                "min": values[0],
                "max": values[-1]
            }
        )

# Use it
jury = JuryEvaluator(judges=[...], strategy=MedianStrategy())
```

### Advanced: Machine Learning Strategy

Use trained model to aggregate:

```python
class LearnedStrategy(AggregationStrategy):
    """
    Uses a trained classifier to predict final score.
    Weights learned from historical data.
    """
    
    def __init__(self, model_path: str):
        import joblib
        self.model = joblib.load(model_path)
    
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult:
        # Extract features: scores + metadata
        features = []
        for s in scores:
            features.extend([
                s.score,
                len(s.reasoning),
                1 if "confident" in s.reasoning.lower() else 0
            ])
        
        # Predict
        prediction = self.model.predict([features])[0]
        confidence = self.model.predict_proba([features])[0].max()
        
        return AggregationResult(
            score=float(prediction),
            confidence=confidence,
            metadata={"strategy": "LearnedStrategy"}
        )
```

---

## Best Practices

### 1. Start Simple

Begin with `MajorityVoting` or `WeightedAverage`. Add complexity only when needed.

### 2. Monitor Confidence

Always check `result.confidence`. Low confidence indicates:
- Judges disagree significantly
- Prompt may be ambiguous
- Edge case that needs human review

### 3. Log Aggregation Metadata

```python
result = jury.evaluate(...)
metadata = result.manifest.metadata['aggregation_metadata']

# Log vote distribution, strategy used, etc.
logger.info(f"Strategy: {metadata['strategy']}")
logger.info(f"Vote distribution: {metadata.get('vote_distribution')}")
```

### 4. Calibrate Weights

For `WeightedSum`, validate weights against ground truth:

```python
# Test different weight configurations
for config in weight_configs:
    jury.set_strategy(WeightedSum(config))
    accuracy = evaluate_against_ground_truth()
    print(f"Config {config}: {accuracy:.2%}")
```

### 5. Handle Ties

Some strategies (like MajorityVoting) can produce ties. Consider fallbacks:

```python
result = jury.evaluate(...)
if result.confidence < 0.5:
    # Fall back to expert model
    jury.set_strategy(WeightedSum({"gpt-4": 1.0}))
    result = jury.evaluate(...)
```

---

## Next Steps

- [API Reference](api-reference.md) - Detailed class documentation
- [Core Concepts](core-concepts.md) - Understanding the evaluation workflow
- [Custom Metrics](custom-metrics.md) - Build domain-specific criteria
- [Examples](../examples/) - See strategies in action
