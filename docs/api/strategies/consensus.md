# Consensus Strategies

Voting-based aggregation implementations for democratic decision-making.

## MajorityVoting

Plurality voting where the most common score wins.

### Class Definition

```python
class MajorityVoting(AggregationStrategy):
    def aggregate(self, scores: List[JudgeScore]) -> AggregationResult
```

### Algorithm

1. Round each score to nearest integer
2. Count frequency of each rounded score
3. Select the most frequent score
4. Calculate confidence as agreement ratio

### Example

```python
from llm_jury.strategies.consensus import MajorityVoting
from llm_jury.core.manifest import JudgeScore

strategy = MajorityVoting()

scores = [
    JudgeScore(score=4.0, reasoning="Good", judge_id="judge1"),
    JudgeScore(score=4.2, reasoning="Good", judge_id="judge2"),  # Rounds to 4
    JudgeScore(score=5.0, reasoning="Excellent", judge_id="judge3"),
    JudgeScore(score=4.1, reasoning="Good", judge_id="judge4"),  # Rounds to 4
]

result = strategy.aggregate(scores)

print(f"Winner: {result.score}")  # 4.0 (3 out of 4 judges)
print(f"Confidence: {result.confidence}")  # 0.75 (75% agreement)
print(f"Metadata: {result.metadata}")
# {
#   "strategy": "MajorityVoting",
#   "vote_distribution": {4: 3, 5: 1},
#   "total_votes": 4
# }
```

### Vote Distribution

Access detailed voting information:

```python
result = strategy.aggregate(scores)
distribution = result.metadata["vote_distribution"]

for score, count in distribution.items():
    print(f"Score {score}: {count} votes ({count/len(scores):.1%})")
```

### Ties

If there's a tie, the first encountered score wins:

```python
scores = [
    JudgeScore(score=4.0, judge_id="j1"),
    JudgeScore(score=4.0, judge_id="j2"),
    JudgeScore(score=5.0, judge_id="j3"),
    JudgeScore(score=5.0, judge_id="j4"),
]

result = strategy.aggregate(scores)
# Winner: 4.0 (first in iteration order)
# Confidence: 0.5 (50% agreement)
```

### When to Use

- ✅ Equal trust in all judges
- ✅ Prefer discrete scores
- ✅ Simple, intuitive decisions
- ✅ Democratic voting model
- ❌ Need fine-grained scores
- ❌ Different judge weights

### Pros & Cons

**Advantages**:
- Simple and intuitive
- Resistant to outliers
- Works well with 3+ judges
- Clear interpretation

**Disadvantages**:
- Loses decimal precision
- No weight differentiation
- Ties less informative

## ConsensusStrategy

Threshold-based voting requiring minimum agreement.

### Class Definition

```python
class ConsensusStrategy(AggregationStrategy):
    def __init__(self, threshold: float = 0.5)
```

### Constructor

#### Parameters

- **threshold** (`float`): Minimum agreement ratio required (0.0-1.0)
  - `0.5`: Majority (>50%)
  - `0.67`: Supermajority (>66%)
  - `0.8`: Strong consensus (>80%)
  - `1.0`: Unanimous

### Algorithm

1. Use MajorityVoting to find candidate score
2. Check if agreement ratio meets threshold
3. Flag in metadata if consensus not reached

### Example

```python
from llm_jury.strategies.consensus import ConsensusStrategy

# Require 70% agreement
strategy = ConsensusStrategy(threshold=0.7)

scores = [
    JudgeScore(score=4.0, judge_id="j1"),
    JudgeScore(score=4.0, judge_id="j2"),
    JudgeScore(score=4.0, judge_id="j3"),
    JudgeScore(score=5.0, judge_id="j4"),
]

result = strategy.aggregate(scores)

print(f"Score: {result.score}")  # 4.0
print(f"Confidence: {result.confidence}")  # 0.75
print(f"Consensus: {result.metadata['consensus_reached']}")  # True (75% >= 70%)
```

### Checking Consensus

```python
result = strategy.aggregate(scores)

if result.metadata["consensus_reached"]:
    print("✓ Strong agreement - proceed with confidence")
else:
    print("⚠ Insufficient consensus - review required")
    # Route to human review or re-evaluate
```

### Failed Consensus

```python
strategy = ConsensusStrategy(threshold=0.8)  # Need 80%

scores = [
    JudgeScore(score=4.0, judge_id="j1"),
    JudgeScore(score=4.0, judge_id="j2"),
    JudgeScore(score=5.0, judge_id="j3"),
    JudgeScore(score=3.0, judge_id="j4"),
]

result = strategy.aggregate(scores)

print(f"Score: {result.score}")  # 4.0 (plurality winner)
print(f"Confidence: {result.confidence}")  # 0.5 (only 50% agreement)
print(f"Consensus: {result.metadata['consensus_reached']}")  # False (50% < 80%)
```

### When to Use

- ✅ High-stakes decisions
- ✅ Need strong agreement
- ✅ Safety-critical applications
- ✅ Quality over coverage
- ❌ Need to process all outputs
- ❌ Low judge count

### Workflow Integration

```python
strategy = ConsensusStrategy(threshold=0.8)

result = jury.evaluate(context, output, metric)

if result.manifest.metadata["consensus_reached"]:
    # Strong consensus - auto-approve
    approve(output)
elif result.confidence < 0.3:
    # Very low agreement - likely problematic
    reject(output)
else:
    # Medium agreement - needs human review
    route_to_human_review(output, result)
```

### Threshold Selection Guide

| Threshold | Meaning | Use Case |
|-----------|---------|----------|
| 0.5 | Simple majority | General decisions |
| 0.67 | Supermajority | Important decisions |
| 0.75 | Strong consensus | High-confidence filtering |
| 0.8 | Very strong | Safety-critical content |
| 0.9 | Near-unanimous | Medical/legal decisions |
| 1.0 | Unanimous | Absolute certainty required |

### Metadata

Both strategies include detailed metadata:

```python
result.metadata = {
    "strategy": "ConsensusStrategy" | "MajorityVoting",
    "vote_distribution": {score: count, ...},
    "total_votes": int,
    "threshold": float,  # ConsensusStrategy only
    "consensus_reached": bool  # ConsensusStrategy only
}
```

## Helper Method

### calculate_agreement

ConsensusStrategy provides a diagnostic helper:

```python
strategy = ConsensusStrategy()

agreement_ratio = strategy.calculate_agreement(scores)
print(f"Agreement: {agreement_ratio:.1%}")
```

Returns the pure inter-judge agreement ratio.

## Comparison

| Aspect | MajorityVoting | ConsensusStrategy |
|--------|---------------|-------------------|
| **Threshold** | None (plurality wins) | Configurable minimum |
| **Flagging** | No | Yes (consensus_reached) |
| **Use Case** | General evaluation | High-confidence decisions |
| **Failure Mode** | Always returns winner | Flags low-confidence |

## Best Practices

### For MajorityVoting

1. **Use with 3+ judges** (odd numbers ideal)
2. **Check confidence** for close decisions
3. **Review low confidence** results (<0.5)
4. **Expect integer scores** due to rounding

### For ConsensusStrategy

1. **Set appropriate threshold** based on risk
2. **Always check consensus_reached** flag
3. **Have fallback plan** for failed consensus
4. **Monitor rejection rate** to tune threshold
5. **Use with 5+ judges** for meaningful thresholds

## Testing

```python
from llm_jury.core.manifest import JudgeScore

# Test majority voting
def test_majority():
    strategy = MajorityVoting()
    
    # Strong agreement
    scores = [JudgeScore(score=4.0, judge_id=f"j{i}") for i in range(5)]
    result = strategy.aggregate(scores)
    assert result.score == 4.0
    assert result.confidence == 1.0
    
    # Split decision
    scores = [
        JudgeScore(score=4.0, judge_id="j1"),
        JudgeScore(score=4.0, judge_id="j2"),
        JudgeScore(score=5.0, judge_id="j3"),
    ]
    result = strategy.aggregate(scores)
    assert result.score == 4.0
    assert result.confidence == 0.67  # 2/3

# Test consensus
def test_consensus():
    strategy = ConsensusStrategy(threshold=0.7)
    
    # Meets threshold
    scores = [
        JudgeScore(score=4.0, judge_id="j1"),
        JudgeScore(score=4.0, judge_id="j2"),
        JudgeScore(score=4.0, judge_id="j3"),
        JudgeScore(score=5.0, judge_id="j4"),
    ]
    result = strategy.aggregate(scores)
    assert result.metadata["consensus_reached"] == True
    
    # Fails threshold
    scores = [
        JudgeScore(score=4.0, judge_id="j1"),
        JudgeScore(score=4.0, judge_id="j2"),
        JudgeScore(score=5.0, judge_id="j3"),
        JudgeScore(score=3.0, judge_id="j4"),
    ]
    result = strategy.aggregate(scores)
    assert result.metadata["consensus_reached"] == False
```

## See Also

- [AggregationStrategy (Base)](base.md)
- [Weighted Strategies](weighted.md)
- [JuryEvaluator](../core/evaluator.md)
