# Manifest & Results

Data structures for capturing evaluation results, judge scores, and audit trails.

## JudgeScore

Represents a single evaluation from one judge.

### Definition

```python
@dataclass
class JudgeScore:
    score: float = 0.0
    reasoning: str = ""
    judge_id: str = "unknown"
    metrics_metadata: Dict[str, float] = field(default_factory=dict)
```

### Attributes

- **score** (`float`): The numerical evaluation (normalized or raw)
- **reasoning** (`str`): Textual justification from the judge
- **judge_id** (`str`): Identifier of the judge (e.g., "gpt-4o")
- **metrics_metadata** (`Dict[str, float]`): Sub-metrics if judge evaluated multiple dimensions

### Methods

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Serializes the score to a dictionary.

### Example

```python
score = JudgeScore(
    score=4.5,
    reasoning="The output is well-grounded with minor paraphrasing.",
    judge_id="gpt-4o",
    metrics_metadata={"accuracy": 0.9, "completeness": 0.85}
)

# Serialize
score_dict = score.to_dict()
```

## JuryManifest

Comprehensive audit trail for an evaluation.

### Definition

```python
@dataclass
class JuryManifest:
    individual_scores: List[JudgeScore] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

### Attributes

- **individual_scores** (`List[JudgeScore]`): Raw scores from all judges
- **features** (`Dict[str, Any]`): Extracted text features (word count, complexity, etc.)
- **metadata** (`Dict[str, Any]`): Additional context (strategy used, latency, etc.)
- **timestamp** (`datetime`): When the evaluation occurred

### Methods

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Serializes the manifest for logging/storage.

### Example

```python
manifest = result.manifest

# Access individual scores
for score in manifest.individual_scores:
    print(f"{score.judge_id}: {score.score}")

# Access features
print(f"Word count: {manifest.features['word_count']}")
print(f"Readability: {manifest.features['flesch_reading_ease']}")

# Access metadata
print(f"Strategy: {manifest.metadata['strategy_used']}")
print(f"Timestamp: {manifest.timestamp}")

# Serialize
manifest_dict = manifest.to_dict()
import json
json.dump(manifest_dict, file)
```

## EvaluationResult

The final aggregated result of an evaluation.

### Definition

```python
@dataclass
class EvaluationResult:
    final_score: float = 0.0
    is_valid: bool = False
    confidence: float = 0.0
    manifest: JuryManifest = field(default_factory=JuryManifest)
```

### Attributes

- **final_score** (`float`): Aggregated score from all judges
- **is_valid** (`bool`): Whether the result passed the validity threshold
- **confidence** (`float`): Inter-judge agreement or certainty (0.0-1.0)
- **manifest** (`JuryManifest`): Detailed audit trail

### Methods

#### get_recommendation

```python
def get_recommendation(self) -> str
```

Returns a high-level recommendation based on score and validity.

**Returns**:
- `"REJECT: ..."` if not valid
- `"WARNING: ..."` if valid but low confidence
- `"APPROVE: ..."` if valid with high confidence

### Example

```python
result = jury.evaluate(...)

# High-level results
print(f"Score: {result.final_score}")
print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence:.2%}")

# Get recommendation
print(result.get_recommendation())

# Access full manifest
for score in result.manifest.individual_scores:
    print(f"{score.judge_id}: {score.score} - {score.reasoning}")

# Check features
word_count = result.manifest.features["word_count"]
if word_count < 50:
    print("Output is quite brief")
```

### Validity Logic

By default, `is_valid = True` if normalized final score ≥ 0.5:

```python
normalized_score = metric.normalize(final_score)
is_valid = normalized_score >= 0.5
```

## BatchEvaluationResult

Container for multiple evaluation results.

### Definition

```python
@dataclass
class BatchEvaluationResult:
    results: Dict[str, EvaluationResult] = field(default_factory=dict)
```

### Attributes

- **results** (`Dict[str, EvaluationResult]`): Map of result IDs to their evaluations
  - Key format: `"{item_id}_{metric_name}"`
  - Example: `"response_1_Groundedness"`

### Methods

#### get_score

```python
def get_score(self, metric_name: str) -> float
```

Retrieves the final score for a specific metric.

**Parameters**:
- **metric_name** (`str`): The result key to look up

**Returns**: `float` - The final score, or 0.0 if not found

#### overall_quality

```python
def overall_quality(self) -> float
```

Calculates average of all scores in the batch.

**Returns**: `float` - Mean of all final scores

#### get_manifest

```python
def get_manifest(self) -> Dict[str, Any]
```

Aggregates all manifests into a single dictionary.

**Returns**: `Dict[str, Any]` - Map of result IDs to serialized manifests

### Example

```python
batch_result = jury.evaluate_batch(inputs, metrics)

# Access specific results
score_1 = batch_result.get_score("response_1_Groundedness")
score_2 = batch_result.get_score("response_2_Hallucination")

# Overall quality
quality = batch_result.overall_quality()
print(f"Average quality: {quality:.2f}")

# Iterate all results
for key, result in batch_result.results.items():
    print(f"{key}: {result.final_score} (valid={result.is_valid})")

# Get all manifests
all_manifests = batch_result.get_manifest()
```

## Usage Patterns

### Serialization

```python
import json

result = jury.evaluate(...)

# Serialize for storage
result_dict = {
    "final_score": result.final_score,
    "is_valid": result.is_valid,
    "confidence": result.confidence,
    "manifest": result.manifest.to_dict()
}

with open("evaluation.json", "w") as f:
    json.dump(result_dict, f, indent=2)
```

### Filtering Results

```python
batch_result = jury.evaluate_batch(...)

# Filter high-quality results
high_quality = {
    key: result for key, result in batch_result.results.items()
    if result.final_score >= 4.0 and result.confidence >= 0.7
}

# Filter for review
needs_review = {
    key: result for key, result in batch_result.results.items()
    if result.confidence < 0.5
}
```

### Extracting Reasoning

```python
result = jury.evaluate(...)

# Collect all reasoning
all_reasoning = [
    f"{score.judge_id}: {score.reasoning}"
    for score in result.manifest.individual_scores
]

# Show to user
print("\n".join(all_reasoning))
```

### Feature Analysis

```python
result = jury.evaluate(...)

features = result.manifest.features

# Analyze complexity
if features["flesch_reading_ease"] < 30:
    print("Warning: Output is very difficult to read")

if features["word_count"] < 20:
    print("Warning: Output is very brief")

if features["lexical_diversity"] < 0.5:
    print("Warning: Limited vocabulary used")
```

## See Also

- [JuryEvaluator](evaluator.md)
- [FeatureExtractor](../../docs/features.md)
- [AggregationResult](../strategies/base.md#aggregationresult)
