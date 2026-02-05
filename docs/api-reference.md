# API Reference

Complete reference for all public classes and methods in LLM Jury.

## Table of Contents

- [Core Module](#core-module)
- [Judges Module](#judges-module)
- [Metrics Module](#metrics-module)
- [Strategies Module](#strategies-module)
- [Features Module](#features-module)
- [Tools Module](#tools-module)

---

## Core Module

### JuryEvaluator

**Location**: `llm_jury.core.evaluator`

The central orchestrator for evaluation workflows.

#### Constructor

```python
JuryEvaluator(
    judges: List[Judge],
    strategy: Optional[AggregationStrategy] = None
)
```

**Parameters**:
- `judges`: List of Judge instances to form the panel
- `strategy`: Aggregation method (defaults to `MajorityVoting()`)

**Example**:
```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.strategies.consensus import MajorityVoting

jury = JuryEvaluator(
    judges=[judge1, judge2, judge3],
    strategy=MajorityVoting()
)
```

#### Methods

##### `evaluate()`

Evaluates a single output against a metric.

```python
def evaluate(
    context: Any,
    output: str,
    metric: Metric
) -> EvaluationResult
```

**Parameters**:
- `context`: Source material or context dict with keys like `source_text`, `output_text`
- `output`: The generated text to evaluate
- `metric`: Evaluation criteria (e.g., `GroundednessMetric()`)

**Returns**: `EvaluationResult` with score, validity, confidence, and manifest

**Example**:
```python
result = jury.evaluate(
    context={"source_text": "Paris is in France."},
    output="Paris is the capital of France.",
    metric=GroundednessMetric()
)
```

##### `evaluate_batch()`

Evaluates multiple inputs across multiple metrics.

```python
def evaluate_batch(
    inputs: Dict[str, Dict[str, Any]],
    metrics: List[Metric]
) -> BatchEvaluationResult
```

**Parameters**:
- `inputs`: Map of ID to context dict (must include `output` key)
- `metrics`: List of metrics to apply to each input

**Returns**: `BatchEvaluationResult` with results keyed by `"ItemID_MetricName"`

**Example**:
```python
results = jury.evaluate_batch(
    inputs={
        "doc1": {"output": "Text 1", "source": "Source 1"},
        "doc2": {"output": "Text 2", "source": "Source 2"}
    },
    metrics=[GroundednessMetric(), HallucinationMetric()]
)
```

##### `add_judge()`

Adds a judge to the existing panel.

```python
def add_judge(judge: Judge) -> None
```

##### `set_strategy()`

Updates the aggregation strategy.

```python
def set_strategy(strategy: AggregationStrategy) -> None
```

---

### EvaluationResult

**Location**: `llm_jury.core.manifest`

Container for final evaluation results.

#### Attributes

```python
@dataclass
class EvaluationResult:
    final_score: float          # Aggregated score
    is_valid: bool             # Whether score meets threshold (>0.5 normalized)
    confidence: float          # Inter-judge agreement (0.0-1.0)
    manifest: JuryManifest     # Complete audit trail
```

#### Methods

##### `get_recommendation()`

Returns human-readable recommendation.

```python
def get_recommendation() -> str
```

**Returns**: One of:
- `"APPROVE: The content meets quality standards with high confidence."`
- `"WARNING: Passed threshold, but jury agreement is low."`
- `"REJECT: The content failed to meet the evaluation threshold."`

**Example**:
```python
result = jury.evaluate(...)
print(result.get_recommendation())
```

---

### JuryManifest

**Location**: `llm_jury.core.manifest`

Complete audit trail for an evaluation.

#### Attributes

```python
@dataclass
class JuryManifest:
    individual_scores: List[JudgeScore]  # All judge verdicts
    features: Dict[str, Any]             # Extracted text features
    metadata: Dict[str, Any]             # Aggregation metadata
    timestamp: datetime                  # When evaluation occurred
```

#### Methods

##### `to_dict()`

Serializes manifest for storage/logging.

```python
def to_dict() -> Dict[str, Any]
```

---

### JudgeScore

**Location**: `llm_jury.core.manifest`

Individual judge evaluation result.

#### Attributes

```python
@dataclass
class JudgeScore:
    score: float                      # Numerical verdict
    reasoning: str                    # Textual justification
    judge_id: str                     # Judge identifier
    metrics_metadata: Dict[str, float] # Sub-metric scores (optional)
```

---

## Judges Module

### Judge (Abstract Base)

**Location**: `llm_jury.judges.base`

Base class for all judge implementations.

#### Constructor

```python
Judge(name: str)
```

#### Abstract Methods

##### `evaluate_score()`

Must be implemented by subclasses.

```python
@abstractmethod
def evaluate_score(
    prompt: str,
    context: Any
) -> JudgeScore
```

---

### LLMJudge

**Location**: `llm_jury.judges.llm_judge`

Wraps LangChain models as judges.

#### Constructor

```python
LLMJudge(
    model: Union[BaseChatModel, BaseLanguageModel],
    name: Optional[str] = None
)
```

**Parameters**:
- `model`: Any LangChain model instance
- `name`: Optional identifier (defaults to model class name)

**Example**:
```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

judge1 = LLMJudge(
    model=ChatOpenAI(model="gpt-4"),
    name="gpt-4-judge"
)

judge2 = LLMJudge(
    model=ChatAnthropic(model="claude-3-opus-20240229"),
    name="claude-opus"
)
```

#### Methods

##### `evaluate_score()`

Executes evaluation using the underlying model.

```python
def evaluate_score(
    prompt: str,
    context: Any
) -> JudgeScore
```

**Internal Flow**:
1. Formats context into readable string
2. Constructs system + human messages
3. Invokes LangChain model
4. Parses response using regex/JSON extraction
5. Returns `JudgeScore`

**Output Format Expected from Model**:
```
Score: 4.5
Reasoning: The text is clear and well-structured.
Metrics: {"clarity": 4.0, "coherence": 5.0}
```

---

## Metrics Module

### Metric (Abstract Base)

**Location**: `llm_jury.metrics.base`

Base class for evaluation criteria.

#### Constructor

```python
Metric(
    name: str,
    description: str,
    scale_min: float = 1.0,
    scale_max: float = 5.0
)
```

**Parameters**:
- `name`: Unique metric identifier
- `description`: Human-readable description
- `scale_min`: Minimum possible score
- `scale_max`: Maximum possible score

#### Abstract Methods

##### `get_prompt()`

Generates evaluation instructions for judges. Must be implemented.

```python
@abstractmethod
def get_prompt(context: Any = None) -> str
```

#### Methods

##### `normalize()`

Converts raw scores to [0, 1] range.

```python
def normalize(score: float) -> float
```

**Formula**: `(score - scale_min) / (scale_max - scale_min)`

**Example**:
```python
metric = GroundednessMetric()  # Scale 1-5
normalized = metric.normalize(4.0)  # Returns 0.75
```

##### `aggregate_metrics()`

Aggregates multiple sub-metric scores. Optional override.

```python
def aggregate_metrics(
    metric_scores: Dict[str, float]
) -> float
```

**Default**: Returns average of all values.

---

### GroundednessMetric

**Location**: `llm_jury.metrics.predefined`

Evaluates whether output is supported by source context.

#### Constructor

```python
GroundednessMetric()
```

**Scale**: 1.0 to 5.0

**Scoring**:
- 5: Fully supported by source
- 4: Mostly supported
- 3: Partially supported
- 2: Significant unsupported information
- 1: Largely unrelated or contradictory

**Example**:
```python
from llm_jury.metrics.predefined import GroundednessMetric

metric = GroundednessMetric()
result = jury.evaluate(
    context={"source_text": source, "output_text": output},
    output=output,
    metric=metric
)
```

---

### HallucinationMetric

**Location**: `llm_jury.metrics.predefined`

Detects fabricated or logically inconsistent information.

#### Constructor

```python
HallucinationMetric()
```

**Scale**: 0.0 to 1.0

**Scoring**:
- 0.0: No hallucination (logically sound, factually accurate)
- 0.5: Minor inconsistencies
- 1.0: Definite hallucination (fabrications, contradictions)

**Example**:
```python
from llm_jury.metrics.predefined import HallucinationMetric

metric = HallucinationMetric()
result = jury.evaluate(
    context={"output_text": output, "input_prompt": question},
    output=output,
    metric=metric
)
```

---

## Strategies Module

### AggregationStrategy (Abstract Base)

**Location**: `llm_jury.strategies.base`

Base class for score aggregation methods.

#### Abstract Methods

##### `aggregate()`

Combines judge scores into final verdict. Must be implemented.

```python
@abstractmethod
def aggregate(
    scores: List[JudgeScore]
) -> AggregationResult
```

**Returns**: `AggregationResult(score, confidence, metadata)`

---

### AggregationResult

**Location**: `llm_jury.strategies.base`

Result of aggregation process.

#### Attributes

```python
@dataclass
class AggregationResult:
    score: float              # Final calculated score
    confidence: float         # Agreement/certainty (0.0-1.0)
    metadata: Dict[str, Any]  # Details about calculation
```

---

### MajorityVoting

**Location**: `llm_jury.strategies.consensus`

Plurality voting - most frequent score wins.

#### Constructor

```python
MajorityVoting()
```

#### Methods

##### `aggregate()`

Returns the score chosen by most judges.

```python
def aggregate(
    scores: List[JudgeScore]
) -> AggregationResult
```

**Confidence Calculation**: `winner_count / total_votes`

**Metadata**:
- `strategy`: "MajorityVoting"
- `vote_distribution`: Dict of score frequencies
- `total_votes`: Number of judges

**Example**:
```python
# Scores: [4, 4, 3, 4, 5]
# Result: score=4.0, confidence=0.6 (3/5 judges agreed)
```

---

### ConsensusStrategy

**Location**: `llm_jury.strategies.consensus`

Requires minimum agreement threshold.

#### Constructor

```python
ConsensusStrategy(threshold: float = 0.5)
```

**Parameters**:
- `threshold`: Minimum agreement ratio (0.0-1.0)

#### Methods

##### `aggregate()`

Uses majority voting but flags if threshold not met.

```python
def aggregate(
    scores: List[JudgeScore]
) -> AggregationResult
```

**Metadata**:
- All MajorityVoting metadata
- `threshold`: Required agreement ratio
- `consensus_reached`: Boolean indicating if threshold met

##### `calculate_agreement()`

Helper to compute pure agreement ratio.

```python
def calculate_agreement(
    scores: List[JudgeScore]
) -> float
```

---

### WeightedSum

**Location**: `llm_jury.strategies.weighted`

Weighted average with configurable judge weights.

#### Constructor

```python
WeightedSum(weights: Dict[str, float])
```

**Parameters**:
- `weights`: Map of judge_id to weight value

**Example**:
```python
strategy = WeightedSum({
    "gpt-4": 1.0,
    "gpt-3.5": 0.5,
    "llama-2": 0.3
})
```

#### Methods

##### `aggregate()`

Computes weighted average.

```python
def aggregate(
    scores: List[JudgeScore]
) -> AggregationResult
```

**Formula**: `sum(weight_i * score_i) / sum(weight_i)`

**Confidence**: Ratio of judges with explicit weights

**Metadata**:
- `strategy`: "WeightedSum"
- `total_weight`: Sum of all weights
- `judges_weighted`: Count of judges with explicit weights

---

### WeightedAverage

**Location**: `llm_jury.strategies.weighted`

Simple arithmetic mean (all judges equal weight).

#### Constructor

```python
WeightedAverage()
```

#### Methods

##### `aggregate()`

Returns simple average of all scores.

```python
def aggregate(
    scores: List[JudgeScore]
) -> AggregationResult
```

**Confidence**: `1.0 / (1.0 + variance)` (inverse variance)

**Metadata**:
- `strategy`: "WeightedAverage"
- `variance`: Statistical variance of scores

---

## Features Module

### FeatureExtractor

**Location**: `llm_jury.features.extractor`

Analyzes text to extract quantitative features.

#### Methods

##### `extract_text_metrics()`

Calculates basic structural metrics.

```python
def extract_text_metrics(text: str) -> Dict[str, Any]
```

**Returns**:
```python
{
    "char_count": int,
    "word_count": int,
    "sentence_count": int,
    "paragraph_count": int,
    "compression_ratio": float  # zlib compression ratio
}
```

##### `extract_complexity()`

Calculates linguistic complexity.

```python
def extract_complexity(text: str) -> Dict[str, Any]
```

**Returns**:
```python
{
    "flesch_reading_ease": float,      # Standard readability score
    "lexical_diversity": float,        # Type-token ratio
    "avg_sentence_length": float
}
```

##### `extract_special_words()`

Identifies special linguistic features.

```python
def extract_special_words(text: str) -> Dict[str, Any]
```

**Returns**:
```python
{
    "difficult_word_count": int,       # Words with 3+ syllables
    "modality_verb_count": int,        # can, should, must, etc.
    "shannon_entropy": float           # Information theoretic measure
}
```

**Example**:
```python
from llm_jury.features.extractor import FeatureExtractor

extractor = FeatureExtractor()
features = extractor.extract_text_metrics("Your text here...")
print(f"Word count: {features['word_count']}")
```

---

## Tools Module

### HallucinationShield

**Location**: `llm_jury.tools.shield`

Validates agentic workflow steps to prevent error propagation.

#### Constructor

```python
HallucinationShield(jury_evaluator: JuryEvaluator)
```

**Parameters**:
- `jury_evaluator`: Configured JuryEvaluator instance

#### Methods

##### `validate_step()`

Validates a proposed agent action against context.

```python
def validate_step(
    context_text: str,
    proposed_action: str,
    metric: Optional[Metric] = None
) -> ValidationResult
```

**Parameters**:
- `context_text`: Source context or current state
- `proposed_action`: Agent's proposed next step
- `metric`: Evaluation criteria (defaults to `GroundednessMetric()`)

**Returns**: `ValidationResult`

**Example**:
```python
from llm_jury.tools.shield import HallucinationShield

shield = HallucinationShield(jury_evaluator=jury)

validation = shield.validate_step(
    context_text="Document says X.",
    proposed_action="Agent wants to do Y based on X."
)

if validation.is_valid:
    execute_action()
else:
    print(validation.consensus_reasoning)
```

##### `get_recovery_guidance()`

Provides feedback for rejected actions.

```python
def get_recovery_guidance(
    result: ValidationResult
) -> str
```

**Returns**: Formatted guidance string for the agent

---

### ValidationResult

**Location**: `llm_jury.tools.shield`

Result of shield validation check.

#### Attributes

```python
@dataclass
class ValidationResult:
    is_valid: bool              # Whether action passed threshold
    consensus_reasoning: str    # Aggregated jury feedback
    confidence: float           # Statistical confidence (0.0-1.0)
    metadata: Dict[str, Any]    # Diagnostic information
```

---

## Type Hints

All public APIs use type hints for better IDE support and type checking.

**Common Types**:
```python
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# LangChain types
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
```

---

## Error Handling

### Common Exceptions

**Judge Failures**: If a judge fails (API error, timeout), evaluation continues with remaining judges. Failed judges are logged but don't raise exceptions.

**Empty Score Lists**: If all judges fail, `JuryEvaluator.evaluate()` returns:
```python
EvaluationResult(
    final_score=0.0,
    is_valid=False,
    confidence=0.0,
    manifest=JuryManifest(timestamp=datetime.now())
)
```

**Parsing Errors**: `LLMJudge` returns a default error score:
```python
JudgeScore(
    score=0.0,
    reasoning="SYSTEM ERROR: Failed to generate evaluation. <error>",
    judge_id=judge_name
)
```

---

## Next Steps

- **[Custom Metrics Guide](custom-metrics.md)**: Build your own evaluation criteria
- **[Aggregation Strategies](aggregation-strategies.md)**: Choose the right voting method
- **[Examples](../examples/)**: See complete implementations
