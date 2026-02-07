# Metrics

Metrics define **what** you're evaluating. They generate the prompts that guide judges and provide normalization for scores.

## Overview

A metric consists of:
- **Name**: Unique identifier (e.g., "Groundedness")
- **Description**: What it measures
- **Scale**: Min/max score range (e.g., 1-5)
- **Prompt Generator**: Creates evaluation instructions
- **Normalizer**: Converts scores to [0, 1]

## Built-in Metrics

### Groundedness Metric

Evaluates if output is fully supported by source context. Critical for RAG systems.

```python
from llm_jury.metrics.predefined import GroundednessMetric

metric = GroundednessMetric()

result = jury.evaluate(
    context={
        "source_text": "Paris is the capital of France.",
        "output_text": "The capital of France is Paris."
    },
    output="The capital of France is Paris.",
    metric=metric
)
```

**Scale**: 1-5
- **5**: Fully supported, every claim has clear basis
- **4**: Mostly supported with minor rephrasing
- **3**: Partially supported with some unsupported details
- **2**: Significant unsupported information
- **1**: Largely unrelated or contradictory

**Use cases**:
- RAG system validation
- Fact-checking against sources
- Citation verification

### Hallucination Metric

Detects fabricated information and logical inconsistencies.

```python
from llm_jury.metrics.predefined import HallucinationMetric

metric = HallucinationMetric()

result = jury.evaluate(
    context={
        "input_prompt": "What is the capital of France?",
        "output_text": "The capital of France is Berlin."
    },
    output="The capital of France is Berlin.",
    metric=metric
)
```

**Scale**: 0.0-1.0
- **0.0**: No hallucination, factually accurate
- **0.5**: Minor inconsistencies or ambiguous statements
- **1.0**: Definite hallucination, fabrications or contradictions

**Use cases**:
- General text generation quality
- Chatbot response validation
- Creative writing consistency checks

## Creating Custom Metrics

Inherit from the `Metric` base class:

```python
from llm_jury.metrics.base import Metric

class CoherenceMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Coherence",
            description="Evaluates logical flow and consistency",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context=None):
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
        Evaluate the coherence of the following text on a scale of 1-5.
        
        TEXT: {output}
        
        CRITERIA:
        5: Perfect logical flow, all ideas connected
        4: Good coherence with minor transitions needed
        3: Moderate coherence, some disconnected points
        2: Poor coherence, many logical jumps
        1: Incoherent, contradictory or nonsensical
        
        Provide your score and reasoning.
        """
```

### Domain-Specific Metric

```python
class MedicalAccuracyMetric(Metric):
    def __init__(self):
        super().__init__(
            name="MedicalAccuracy",
            description="Evaluates accuracy of medical information",
            scale_min=0.0,
            scale_max=10.0
        )
    
    def get_prompt(self, context=None):
        return """
        As a medical expert, evaluate the accuracy of this medical information.
        
        GUIDELINES:
        - Verify terminology correctness
        - Check for dangerous misinformation
        - Assess treatment appropriateness
        
        Score 0-10 where:
        10: Perfectly accurate medical information
        5: Some accuracy but notable errors
        0: Dangerous misinformation
        """
```

### Composite Metric

Evaluate multiple aspects simultaneously:

```python
class QualityMetric(Metric):
    def __init__(self):
        super().__init__(
            name="OverallQuality",
            description="Combines coherence, relevance, and accuracy",
            scale_min=0.0,
            scale_max=1.0
        )
    
    def get_prompt(self, context=None):
        return """
        Evaluate this text on three dimensions:
        1. Coherence (logical flow)
        2. Relevance (answers the question)
        3. Accuracy (factually correct)
        
        Return scores for each as JSON:
        {
            "coherence": 0.8,
            "relevance": 0.9,
            "accuracy": 0.7
        }
        
        Overall score is the average.
        """
    
    def aggregate_metrics(self, metric_scores):
        # Custom aggregation logic
        weights = {"coherence": 0.3, "relevance": 0.4, "accuracy": 0.3}
        return sum(score * weights[name] for name, score in metric_scores.items())
```

## Metric Features

### Score Normalization

All metrics can normalize scores to [0, 1]:

```python
metric = GroundednessMetric()  # Scale: 1-5

raw_score = 4.0
normalized = metric.normalize(raw_score)  # 0.75
```

This enables fair comparison across different scales:

```python
# Compare metrics with different scales
groundedness = GroundednessMetric()  # 1-5
hallucination = HallucinationMetric()  # 0-1

score1_normalized = groundedness.normalize(4.0)  # 0.75
score2_normalized = hallucination.normalize(0.25)  # 0.25
```

### Context Injection

Metrics can dynamically use context:

```python
def get_prompt(self, context=None):
    source = context.get("source_text", "")
    output = context.get("output_text", "")
    query = context.get("user_query", "")
    
    return f"""
    User asked: {query}
    Source says: {source}
    Model generated: {output}
    
    Evaluate if the output answers the query using the source.
    """
```

## Metric Selection Guide

### For RAG Systems
Use **GroundednessMetric** to ensure outputs are supported by retrieved documents.

```python
from llm_jury.metrics.predefined import GroundednessMetric
metric = GroundednessMetric()
```

### For Chatbots
Use **HallucinationMetric** to catch fabricated responses.

```python
from llm_jury.metrics.predefined import HallucinationMetric
metric = HallucinationMetric()
```

### For Content Generation
Create custom metrics for style, tone, or brand voice.

```python
class BrandVoiceMetric(Metric):
    def get_prompt(self, context=None):
        return "Rate how well this matches our brand's friendly, professional tone..."
```

### For Technical Writing
Evaluate clarity, accuracy, and completeness.

```python
class TechnicalClarityMetric(Metric):
    def get_prompt(self, context=None):
        return "Evaluate technical accuracy and clarity for a developer audience..."
```

## Batch Evaluation with Multiple Metrics

Evaluate the same output against multiple criteria:

```python
metrics = [
    GroundednessMetric(),
    HallucinationMetric(),
    CoherenceMetric()
]

inputs = {
    "output1": {
        "source_text": "...",
        "output": "..."
    }
}

batch_result = jury.evaluate_batch(inputs, metrics)

# Access results by metric
groundedness_score = batch_result.get_score("output1_Groundedness")
hallucination_score = batch_result.get_score("output1_Hallucination")
```

## Advanced Patterns

### Conditional Metrics

```python
class AdaptiveMetric(Metric):
    def get_prompt(self, context=None):
        output_length = len(context.get("output_text", ""))
        
        if output_length < 50:
            return "Evaluate this brief response for accuracy..."
        else:
            return "Evaluate this detailed response for coherence and depth..."
```

### Multi-Language Metrics

```python
class MultilingualQualityMetric(Metric):
    def get_prompt(self, context=None):
        language = context.get("language", "en")
        
        prompts = {
            "en": "Evaluate this English text...",
            "es": "Evalúa este texto en español...",
            "fr": "Évaluez ce texte français..."
        }
        
        return prompts.get(language, prompts["en"])
```

## Best Practices

1. **Clear Scoring Criteria**: Define each point on your scale explicitly
2. **Consistent Scales**: Use 1-5 or 0-1 for easy comparison
3. **Specific Instructions**: Tell judges exactly what to look for
4. **Context Awareness**: Use all available context in prompts
5. **Test Prompts**: Verify judges understand your criteria
6. **Document Scales**: Explain what each score means

## Metric Metadata

Access metric information:

```python
metric = GroundednessMetric()

print(metric.name)         # "Groundedness"
print(metric.description)  # "Measures if the answer..."
print(metric.scale_min)    # 1.0
print(metric.scale_max)    # 5.0
```

## Next Steps

- Learn about [Judges](judges.md) that evaluate metrics
- Explore [Aggregation Strategies](strategies.md)
- See [Examples](examples.md) of metric usage
