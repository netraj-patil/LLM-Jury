# Metric (Base)

Abstract base class for evaluation criteria and scoring logic.

## Class Definition

```python
from abc import ABC, abstractmethod

class Metric(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        scale_min: float = 1.0,
        scale_max: float = 5.0
    )
```

## Constructor

### Parameters

- **name** (`str`): Unique identifier (e.g., "Groundedness")
- **description** (`str`): Human-readable explanation of what this metric measures
- **scale_min** (`float`): Minimum possible score (default: 1.0)
- **scale_max** (`float`): Maximum possible score (default: 5.0)

### Example

```python
from llm_jury.metrics.base import Metric

metric = Metric(
    name="MyMetric",
    description="Measures quality of responses",
    scale_min=0.0,
    scale_max=10.0
)
```

## Abstract Methods

### get_prompt

```python
@abstractmethod
def get_prompt(self, context: Any = None) -> str
```

Generates the evaluation instruction for judges.

#### Parameters

- **context** (`Any`, optional): Data to inject into the prompt
  - Typically a dict with keys like `source_text`, `output_text`, `user_query`

#### Returns

`str`: Complete prompt instructing judges what to evaluate and how to score

#### Example Implementation

```python
class CustomMetric(Metric):
    def get_prompt(self, context=None):
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
        Evaluate this text on a scale of 1-5:
        
        TEXT: {output}
        
        CRITERIA:
        5: Excellent
        3: Acceptable
        1: Poor
        
        Provide score and reasoning.
        """
```

## Methods

### normalize

```python
def normalize(self, score: float) -> float
```

Converts a raw score to [0, 1] range.

#### Parameters

- **score** (`float`): Raw score from a judge

#### Returns

`float`: Normalized value between 0.0 and 1.0

#### Formula

```python
(score - scale_min) / (scale_max - scale_min)
```

#### Example

```python
metric = Metric(name="Test", description="Test", scale_min=1.0, scale_max=5.0)

# Raw score of 3 on 1-5 scale
normalized = metric.normalize(3.0)  # Returns 0.5

# Raw score of 5 on 1-5 scale
normalized = metric.normalize(5.0)  # Returns 1.0

# Different scale
metric2 = Metric(name="Test", description="Test", scale_min=0.0, scale_max=10.0)
normalized2 = metric2.normalize(7.0)  # Returns 0.7
```

#### Clamping

Scores are automatically clamped to the scale range:

```python
metric = Metric(name="Test", description="Test", scale_min=1.0, scale_max=5.0)

# Score above max
metric.normalize(6.0)  # Returns 1.0 (clamped to 5.0)

# Score below min
metric.normalize(0.0)  # Returns 0.0 (clamped to 1.0)
```

### aggregate_metrics

```python
def aggregate_metrics(self, metric_scores: Dict[str, float]) -> float
```

Optional method to combine multiple sub-metric scores.

#### Parameters

- **metric_scores** (`Dict[str, float]`): Map of sub-metric names to scores

#### Returns

`float`: Aggregated score

#### Default Implementation

Returns simple average:

```python
sum(metric_scores.values()) / len(metric_scores)
```

#### Custom Implementation

```python
class WeightedMetric(Metric):
    def aggregate_metrics(self, metric_scores):
        weights = {
            "accuracy": 0.5,
            "completeness": 0.3,
            "clarity": 0.2
        }
        
        return sum(
            score * weights.get(name, 1.0)
            for name, score in metric_scores.items()
        ) / sum(weights.values())
```

## Attributes

### name

```python
self.name: str
```

The metric's unique identifier.

### description

```python
self.description: str
```

Human-readable explanation of the metric.

### scale_min

```python
self.scale_min: float
```

Minimum possible raw score.

### scale_max

```python
self.scale_max: float
```

Maximum possible raw score.

## Implementing Custom Metrics

### Basic Example

```python
from llm_jury.metrics.base import Metric

class ClarityMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Clarity",
            description="Measures how clear and understandable the text is",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context=None):
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
        Rate the clarity of this text on a scale of 1-5:
        
        TEXT: {output}
        
        5: Crystal clear, easy to understand
        4: Clear with minor ambiguities
        3: Moderately clear
        2: Somewhat confusing
        1: Very unclear or confusing
        
        Provide your score and reasoning.
        """
```

### Context-Aware Metric

```python
class RelevanceMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Relevance",
            description="Measures relevance to the user query",
            scale_min=0.0,
            scale_max=1.0
        )
    
    def get_prompt(self, context=None):
        query = context.get("user_query", "") if isinstance(context, dict) else ""
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
        USER QUERY: {query}
        
        RESPONSE: {output}
        
        Rate how relevant the response is to the query (0.0-1.0):
        1.0: Directly answers the query
        0.5: Partially relevant
        0.0: Completely irrelevant
        """
```

### Multi-Dimensional Metric

```python
class ComprehensiveQualityMetric(Metric):
    def __init__(self):
        super().__init__(
            name="ComprehensiveQuality",
            description="Evaluates multiple quality dimensions",
            scale_min=0.0,
            scale_max=1.0
        )
    
    def get_prompt(self, context=None):
        return """
        Evaluate on these dimensions and return JSON:
        
        {
            "accuracy": <0.0-1.0>,
            "completeness": <0.0-1.0>,
            "clarity": <0.0-1.0>
        }
        """
    
    def aggregate_metrics(self, metric_scores):
        # Custom weighted aggregation
        weights = {"accuracy": 0.5, "completeness": 0.3, "clarity": 0.2}
        return sum(
            score * weights.get(name, 1.0)
            for name, score in metric_scores.items()
        )
```

## String Representation

```python
metric = ClarityMetric()
print(metric)
# <ClarityMetric(name='Clarity', scale=[1.0, 5.0])>
```

## Best Practices

1. **Clear Scoring Criteria**: Define what each point on the scale means
2. **Consistent Scales**: Use 1-5 or 0-1 for easy comparison
3. **Context Injection**: Use all available context in prompts
4. **Explicit Instructions**: Tell judges exactly what to look for
5. **Test Prompts**: Verify judges understand your criteria
6. **Document Scale**: Explain the meaning of scores

## Common Scales

### 1-5 Star Rating

```python
scale_min=1.0, scale_max=5.0
```
Standard for discrete ratings.

### 0-1 Probability

```python
scale_min=0.0, scale_max=1.0
```
Good for yes/no or likelihood questions.

### 0-10 Detailed

```python
scale_min=0.0, scale_max=10.0
```
More granular scoring.

## See Also

- [Predefined Metrics](predefined.md)
- [JuryEvaluator](../core/evaluator.md)
- [Judge](../judges/base.md)
