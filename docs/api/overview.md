# API Reference

Complete API documentation for LLM Jury.

## Modules

### Core
- **[JuryEvaluator](core/evaluator.md)** - Main orchestration engine
- **[Manifest & Results](core/manifest.md)** - Data structures for results

### Judges
- **[Judge (Base)](judges/base.md)** - Abstract judge interface
- **[LLMJudge](judges/llm_judge.md)** - LangChain model integration

### Metrics
- **[Metric (Base)](metrics/base.md)** - Abstract metric interface
- **[Predefined Metrics](metrics/predefined.md)** - Standard evaluation criteria

### Strategies
- **[AggregationStrategy (Base)](strategies/base.md)** - Abstract strategy interface
- **[Consensus Strategies](strategies/consensus.md)** - Voting-based aggregation
- **[Weighted Strategies](strategies/weighted.md)** - Mathematical aggregation

## Quick Reference

### Main Classes

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric, HallucinationMetric
from llm_jury.strategies.consensus import MajorityVoting, ConsensusStrategy
from llm_jury.strategies.weighted import WeightedSum, WeightedAverage
from llm_jury.tools.shield import HallucinationShield
```

### Data Classes

```python
from llm_jury.core.manifest import (
    JudgeScore,
    JuryManifest,
    EvaluationResult,
    BatchEvaluationResult
)
from llm_jury.strategies.base import AggregationResult
from llm_jury.tools.shield import ValidationResult
```

### Feature Extraction

```python
from llm_jury.features.extractor import FeatureExtractor
```

## Type Signatures

### Core Types

```python
from typing import List, Dict, Any, Optional

# Context can be a string or dictionary
Context = Union[str, Dict[str, Any]]

# Judge names and IDs
JudgeName = str
JudgeID = str

# Scores
Score = float  # Typically 0.0-5.0 or 0.0-1.0
NormalizedScore = float  # Always 0.0-1.0
Confidence = float  # 0.0-1.0
```

## Common Patterns

### Basic Evaluation

```python
result: EvaluationResult = jury.evaluate(
    context: Context,
    output: str,
    metric: Metric
)
```

### Batch Evaluation

```python
batch_result: BatchEvaluationResult = jury.evaluate_batch(
    inputs: Dict[str, Dict[str, Any]],
    metrics: List[Metric]
)
```

### Judge Creation

```python
judge: Judge = LLMJudge(
    model: Union[BaseChatModel, BaseLanguageModel],
    name: Optional[str] = None
)
```

### Strategy Selection

```python
strategy: AggregationStrategy = MajorityVoting()
# or
strategy: AggregationStrategy = WeightedSum(weights: Dict[str, float])
# or
strategy: AggregationStrategy = ConsensusStrategy(threshold: float)
```

## Return Types

### EvaluationResult

```python
@dataclass
class EvaluationResult:
    final_score: float
    is_valid: bool
    confidence: float
    manifest: JuryManifest
```

### JudgeScore

```python
@dataclass
class JudgeScore:
    score: float
    reasoning: str
    judge_id: str
    metrics_metadata: Dict[str, float]
```

### AggregationResult

```python
@dataclass
class AggregationResult:
    score: float
    confidence: float
    metadata: Dict[str, Any]
```

## Navigation

Browse the API documentation:

- **Core**: Orchestration and results
- **Judges**: Evaluation implementations
- **Metrics**: Criteria definitions
- **Strategies**: Score aggregation

## Version Information

API version: 1.0.0  
Stability: Stable  
Breaking changes: Semver-compliant
