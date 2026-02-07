# JuryEvaluator

The central orchestration engine that coordinates judges, metrics, and aggregation strategies.

## Class Definition

```python
class JuryEvaluator:
    def __init__(
        self, 
        judges: List[Judge], 
        strategy: Optional[AggregationStrategy] = None
    )
```

## Constructor

### Parameters

- **judges** (`List[Judge]`): List of judge instances to form the evaluation panel
- **strategy** (`Optional[AggregationStrategy]`): Aggregation method for combining scores. Defaults to `MajorityVoting()` if not provided

### Example

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.strategies.consensus import MajorityVoting
from langchain_openai import ChatOpenAI

judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5"),
]

jury = JuryEvaluator(
    judges=judges,
    strategy=MajorityVoting()
)
```

## Methods

### evaluate

Evaluates a single output against a specific metric.

```python
def evaluate(
    self,
    context: Any,
    output: str,
    metric: Metric
) -> EvaluationResult
```

#### Parameters

- **context** (`Any`): Source material, input prompt, or dictionary containing evaluation context
  - Can be a string, dict, or any object
  - If dict, should include keys like `source_text`, `output_text`, `user_query`
- **output** (`str`): The model-generated text to evaluate
- **metric** (`Metric`): The evaluation criteria (e.g., `GroundednessMetric()`)

#### Returns

`EvaluationResult`: Complete evaluation with score, validity, confidence, and manifest

#### Process

1. **Feature Extraction**: Analyzes output text for complexity and metrics
2. **Prompt Generation**: Uses metric to create evaluation instructions
3. **Parallel Judging**: All judges evaluate simultaneously
4. **Score Normalization**: Standardizes scores to [0, 1] range
5. **Aggregation**: Combines scores using the selected strategy
6. **Manifest Creation**: Packages everything into audit trail

#### Example

```python
from llm_jury.metrics.predefined import GroundednessMetric

result = jury.evaluate(
    context={
        "source_text": "Paris is the capital of France.",
        "output_text": "The capital of France is Paris."
    },
    output="The capital of France is Paris.",
    metric=GroundednessMetric()
)

print(f"Score: {result.final_score}")
print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")

# Access individual judge scores
for score in result.manifest.individual_scores:
    print(f"{score.judge_id}: {score.score} - {score.reasoning}")
```

### evaluate_batch

Evaluates multiple outputs across multiple metrics.

```python
def evaluate_batch(
    self,
    inputs: Dict[str, Dict[str, Any]],
    metrics: List[Metric]
) -> BatchEvaluationResult
```

#### Parameters

- **inputs** (`Dict[str, Dict[str, Any]]`): Map of IDs to context dictionaries
  - Each value must include `output` and `source_text` keys
  - ID format: `"item1"`, `"output_1"`, etc.
- **metrics** (`List[Metric]`): List of metrics to apply to each input

#### Returns

`BatchEvaluationResult`: Container with all results mapped by `"{item_id}_{metric_name}"`

#### Example

```python
inputs = {
    "response_1": {
        "source_text": "Context for response 1...",
        "output": "Generated text 1..."
    },
    "response_2": {
        "source_text": "Context for response 2...",
        "output": "Generated text 2..."
    }
}

metrics = [
    GroundednessMetric(),
    HallucinationMetric()
]

batch_result = jury.evaluate_batch(inputs, metrics)

# Access specific results
score_1_ground = batch_result.get_score("response_1_Groundedness")
score_2_halluc = batch_result.get_score("response_2_Hallucination")

# Overall quality
overall = batch_result.overall_quality()
```

### add_judge

Adds a new judge to the existing panel.

```python
def add_judge(self, judge: Judge) -> None
```

#### Parameters

- **judge** (`Judge`): Judge instance to add

#### Example

```python
jury = JuryEvaluator(judges=[judge1, judge2])

# Add another judge later
jury.add_judge(judge3)

# Now jury has 3 judges
```

### set_strategy

Updates the aggregation strategy.

```python
def set_strategy(self, strategy: AggregationStrategy) -> None
```

#### Parameters

- **strategy** (`AggregationStrategy`): New aggregation method

#### Example

```python
from llm_jury.strategies.weighted import WeightedSum

# Start with majority voting
jury = JuryEvaluator(judges=judges)

# Switch to weighted sum
jury.set_strategy(WeightedSum(weights={
    "gpt-4": 1.5,
    "gpt-3.5": 1.0
}))
```

## Attributes

### judges

```python
self.judges: List[Judge]
```

List of judge instances in the panel. Can be modified directly or via `add_judge()`.

### strategy

```python
self.strategy: AggregationStrategy
```

Current aggregation strategy. Can be modified directly or via `set_strategy()`.

### feature_extractor

```python
self.feature_extractor: FeatureExtractor
```

Instance of FeatureExtractor used for text analysis. Created automatically.

## Error Handling

### Judge Failures

Individual judge failures don't crash the evaluation:

```python
# If a judge fails, it's logged but evaluation continues
result = jury.evaluate(...)

# Check if all judges succeeded
num_judges = len(jury.judges)
num_scores = len(result.manifest.individual_scores)

if num_scores < num_judges:
    print(f"Warning: {num_judges - num_scores} judges failed")
```

### No Valid Scores

If all judges fail:

```python
result = jury.evaluate(...)

if not result.manifest.individual_scores:
    # All judges failed
    assert result.final_score == 0.0
    assert result.is_valid == False
    assert result.confidence == 0.0
```

## Performance

### Concurrency

Judges execute in parallel using `ThreadPoolExecutor`:

```python
# All judges run simultaneously
with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.judges)) as executor:
    # Submit all judges at once
    futures = [executor.submit(judge.evaluate_score, ...) for judge in judges]
```

### Latency

Total latency ≈ slowest judge (not sum of all judges):

```python
# 3 judges × 500ms each = ~500ms total (not 1500ms)
```

## Best Practices

1. **Use 3-5 judges** for balance of accuracy and speed
2. **Set strategy explicitly** for clarity
3. **Check confidence** before trusting results
4. **Access manifests** for debugging
5. **Handle failures** gracefully

## See Also

- [EvaluationResult](manifest.md#evaluationresult)
- [BatchEvaluationResult](manifest.md#batchevaluationresult)
- [Judge](../judges/base.md)
- [Metric](../metrics/base.md)
- [AggregationStrategy](../strategies/base.md)
