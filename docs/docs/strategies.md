# Aggregation Strategies

Strategies combine multiple judge scores into a single, reliable verdict. Choosing the right strategy is crucial for your use case.

## Overview

After judges evaluate an output, their scores must be aggregated. Different strategies handle disagreements differently:

- **Majority Voting**: Democratic - most common score wins
- **Weighted Sum**: Some judges trusted more than others
- **Consensus**: Requires threshold of agreement
- **Weighted Average**: Statistical mean with confidence

## Majority Voting

The most common score becomes the final score.

### Usage

```python
from llm_jury.strategies.consensus import MajorityVoting

strategy = MajorityVoting()
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

### How It Works

1. Rounds scores to nearest integer
2. Counts frequency of each score
3. Selects the most frequent score
4. Confidence = agreement ratio

### Example

```
Judge 1: 4.0
Judge 2: 4.2  (rounds to 4)
Judge 3: 5.0
Judge 4: 4.1  (rounds to 4)

Winner: 4 (3 votes)
Confidence: 0.75 (3 out of 4 judges)
```

### When to Use

- You want equal weight for all judges
- Prefer discrete, interpretable scores
- Need democratic decision-making
- Have 3+ judges (works best with odd numbers)

### Pros/Cons

✅ Simple and intuitive  
✅ Resistant to outliers  
✅ Clear interpretation  
❌ Loses nuance (4.1 = 3.9)  
❌ Requires rounding  

## Weighted Sum

Assigns different importance to each judge.

### Usage

```python
from llm_jury.strategies.weighted import WeightedSum

strategy = WeightedSum(weights={
    "gpt-4o": 1.5,      # Most trusted
    "claude-3": 1.0,    # Standard weight
    "llama-3": 0.5      # Less trusted
})

jury = JuryEvaluator(judges=judges, strategy=strategy)
```

### How It Works

Formula: `score = Σ(weight_i × score_i) / Σ(weight_i)`

### Example

```
Judge       Score   Weight  Contribution
gpt-4o      4.5     1.5     6.75
claude-3    4.0     1.0     4.00
llama-3     3.5     0.5     1.75

Final: (6.75 + 4.00 + 1.75) / (1.5 + 1.0 + 0.5) = 4.17
```

### When to Use

- Some models are more reliable for your task
- You have historical accuracy data
- Want to leverage model strengths
- Need fine-grained scores

### Determining Weights

**Based on benchmarks**:
```python
# Higher scores on your validation set = higher weight
weights = {
    "gpt-4o": 1.5,      # 90% accuracy
    "claude-3": 1.2,    # 85% accuracy  
    "gemini": 1.0,      # 80% accuracy
}
```

**Based on cost**:
```python
# More expensive models get higher weight
weights = {
    "gpt-4o": 2.0,      # Premium model
    "gpt-3.5": 0.5,     # Cheap model
}
```

### Pros/Cons

✅ Leverages model strengths  
✅ Preserves fine-grained scores  
✅ Flexible  
❌ Requires tuning weights  
❌ Can over-rely on one judge  

## Consensus Strategy

Requires a minimum percentage of judges to agree.

### Usage

```python
from llm_jury.strategies.consensus import ConsensusStrategy

strategy = ConsensusStrategy(threshold=0.7)  # 70% must agree
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

### How It Works

1. Uses majority voting to find candidate score
2. Checks if agreement ratio ≥ threshold
3. Flags in metadata if consensus not reached

### Example

```
Judge 1: 4
Judge 2: 4
Judge 3: 4
Judge 4: 5

Agreement: 75% (3/4 agree on 4)
Threshold: 70%
Result: Consensus reached ✓
```

### When to Use

- High-stakes decisions (medical, legal, safety)
- Need strong agreement before acting
- Want to flag uncertain cases
- Quality over coverage

### Checking Consensus

```python
result = jury.evaluate(...)

# Check metadata
consensus = result.manifest.metadata["consensus_reached"]

if not consensus:
    print("WARNING: Judges disagree!")
    # Route to human review
```

### Pros/Cons

✅ High confidence in results  
✅ Identifies uncertainty  
✅ Good for safety-critical apps  
❌ May reject valid outputs  
❌ Needs more judges  

## Weighted Average

Simple arithmetic mean with variance-based confidence.

### Usage

```python
from llm_jury.strategies.weighted import WeightedAverage

strategy = WeightedAverage()
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

### How It Works

- **Score**: Mean of all judge scores
- **Confidence**: `1 / (1 + variance)` (low variance = high confidence)

### Example

```
Scores: [4.5, 4.3, 4.6, 4.4]
Mean: 4.45
Variance: 0.015
Confidence: 0.985 (very high)

Scores: [5.0, 2.0, 4.0, 3.0]
Mean: 3.5
Variance: 1.25
Confidence: 0.44 (low - judges disagree)
```

### When to Use

- Want continuous scores
- Need statistical measures
- All judges equally trusted
- Standard evaluation scenarios

### Pros/Cons

✅ Simple and standard  
✅ Variance = confidence metric  
✅ No configuration needed  
❌ Sensitive to outliers  
❌ Equal weight only  

## Comparison Table

| Strategy | Pros | Best For | Configuration |
|----------|------|----------|---------------|
| **Majority Voting** | Simple, robust | General use, discrete scores | None |
| **Weighted Sum** | Flexible, leverages strengths | Unequal judge quality | Requires weights |
| **Consensus** | High confidence | High-stakes decisions | Requires threshold |
| **Weighted Average** | Statistical, continuous | Standard evaluation | None |

## Choosing a Strategy

### Decision Tree

```
Do you trust all judges equally?
├─ Yes
│  └─ Need high confidence?
│     ├─ Yes → ConsensusStrategy(threshold=0.8)
│     └─ No → WeightedAverage()
└─ No
   └─ Have historical accuracy data?
      ├─ Yes → WeightedSum(weights={...})
      └─ No → MajorityVoting()
```

### Use Case Examples

**RAG System (Quality Assurance)**:
```python
# Want reliable consensus on groundedness
strategy = ConsensusStrategy(threshold=0.7)
```

**Content Moderation (Safety)**:
```python
# Need very high agreement for blocking content
strategy = ConsensusStrategy(threshold=0.9)
```

**Research Benchmarking**:
```python
# Statistical comparison across models
strategy = WeightedAverage()
```

**Production System (Cost-Optimized)**:
```python
# Trust expensive model more than cheap ones
strategy = WeightedSum(weights={
    "gpt-4o": 2.0,
    "gpt-3.5": 0.5
})
```

## Custom Strategies

Create your own aggregation logic:

```python
from llm_jury.strategies.base import AggregationStrategy, AggregationResult

class MedianStrategy(AggregationStrategy):
    """Uses median instead of mean to resist outliers."""
    
    def aggregate(self, scores):
        values = sorted([s.score for s in scores])
        n = len(values)
        
        if n == 0:
            return AggregationResult(score=0.0, confidence=0.0)
        
        # Calculate median
        if n % 2 == 0:
            median = (values[n//2 - 1] + values[n//2]) / 2
        else:
            median = values[n//2]
        
        # Confidence based on IQR (interquartile range)
        q1, q3 = values[n//4], values[3*n//4]
        iqr = q3 - q1
        confidence = 1.0 / (1.0 + iqr)
        
        return AggregationResult(
            score=median,
            confidence=confidence,
            metadata={"strategy": "Median", "iqr": iqr}
        )
```

### Ensemble Strategy

Combine multiple strategies:

```python
class EnsembleStrategy(AggregationStrategy):
    def aggregate(self, scores):
        # Get results from multiple strategies
        majority = MajorityVoting().aggregate(scores)
        average = WeightedAverage().aggregate(scores)
        
        # Combine them
        final_score = (majority.score + average.score) / 2
        final_conf = min(majority.confidence, average.confidence)
        
        return AggregationResult(
            score=final_score,
            confidence=final_conf,
            metadata={"strategies": ["Majority", "Average"]}
        )
```

## Changing Strategies Dynamically

```python
jury = JuryEvaluator(judges=judges)

# Start with majority voting
jury.set_strategy(MajorityVoting())
result1 = jury.evaluate(...)

# Switch to consensus for important decision
jury.set_strategy(ConsensusStrategy(threshold=0.8))
result2 = jury.evaluate(...)

# Use weighted for final production
jury.set_strategy(WeightedSum(weights={...}))
result3 = jury.evaluate(...)
```

## Best Practices

1. **Start simple**: Begin with MajorityVoting or WeightedAverage
2. **Validate choices**: Test strategies on validation data
3. **Monitor confidence**: Low confidence = need human review
4. **Document decisions**: Record why you chose each strategy
5. **A/B test**: Compare strategies in production

## Next Steps

- Understand [Core Concepts](core-concepts.md)
- Learn about [Judges](judges.md) and [Metrics](metrics.md)
- See [Examples](examples.md) of strategy selection
