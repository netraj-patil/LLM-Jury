# Predefined Metrics

Standard metric implementations for common evaluation tasks.

## GroundednessMetric

Evaluates whether model output is fully supported by source context.

### Class Definition

```python
class GroundednessMetric(Metric):
    def __init__(self)
```

### Properties

- **Name**: "Groundedness"
- **Description**: "Measures if the answer is derived solely from the source context"
- **Scale**: 1.0 - 5.0

### Scoring Criteria

- **5**: Output fully supported by source, every claim has clear basis
- **4**: Mostly supported with minor rephrasing that preserves meaning
- **3**: Partially supported but includes minor unsupported details
- **2**: Contains significant information not present in source
- **1**: Largely unrelated to source or contradicts it

### Expected Context

```python
context = {
    "source_text": str,    # The retrieved context or reference document
    "output_text": str     # The model's generated answer
}
```

### Example Usage

```python
from llm_jury.metrics.predefined import GroundednessMetric
from llm_jury.core.evaluator import JuryEvaluator

metric = GroundednessMetric()

result = jury.evaluate(
    context={
        "source_text": "The Eiffel Tower is located in Paris, France.",
        "output_text": "The Eiffel Tower is in Paris."
    },
    output="The Eiffel Tower is in Paris.",
    metric=metric
)

print(f"Groundedness Score: {result.final_score}/5.0")
```

### Use Cases

- **RAG System Validation**: Ensure generated answers cite retrieved documents
- **Fact-Checking**: Verify claims against sources
- **Citation Verification**: Check if statements have source support
- **Hallucination Prevention**: Detect unsupported generation

### Prompt Structure

The metric generates prompts that:
1. Present the source text
2. Present the model output
3. Ask judges to verify factual support
4. Provide clear 1-5 scoring rubric

## HallucinationMetric

Evaluates presence of fabricated information or logical inconsistencies.

### Class Definition

```python
class HallucinationMetric(Metric):
    def __init__(self)
```

### Properties

- **Name**: "Hallucination"
- **Description**: "Measures the presence of fabricated or logically inconsistent information"
- **Scale**: 0.0 - 1.0

### Scoring Criteria

- **0.0**: No hallucination, text is logically sound and factually accurate
- **0.5**: Minor inconsistencies or ambiguous statements
- **1.0**: Definite hallucination with fabrications, contradictions, or nonsense

### Expected Context

```python
context = {
    "output_text": str,      # The model's generated answer to check
    "input_prompt": str      # The original user question (optional but helpful)
}
```

### Example Usage

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

print(f"Hallucination Score: {result.final_score:.2f}")
print(f"Has Hallucination: {result.final_score > 0.5}")
```

### Use Cases

- **General Text Generation**: Check for fabricated facts
- **Chatbot Responses**: Ensure factual consistency
- **Creative Writing**: Verify internal consistency
- **World Knowledge**: Validate against common knowledge

### Interpretation

Since this is a "badness" metric (higher = worse):

```python
if result.final_score > 0.7:
    print("High hallucination risk - reject")
elif result.final_score > 0.3:
    print("Some hallucination detected - review")
else:
    print("Low hallucination risk - accept")
```

### Prompt Structure

The metric generates prompts that:
1. Present the user input (if available)
2. Present the model output
3. Ask judges to identify fabrications or inconsistencies
4. Provide 0.0-1.0 scoring scale

## Comparison

| Aspect | GroundednessMetric | HallucinationMetric |
|--------|-------------------|-------------------|
| **Focus** | Source-based support | Logical consistency |
| **Requires Source** | Yes | No |
| **Scale** | 1-5 (higher = better) | 0-1 (lower = better) |
| **Use Case** | RAG systems | General generation |
| **Question** | "Is it supported?" | "Is it fabricated?" |

## Combined Usage

Use both metrics together for comprehensive evaluation:

```python
from llm_jury.metrics.predefined import GroundednessMetric, HallucinationMetric

metrics = [
    GroundednessMetric(),
    HallucinationMetric()
]

# Batch evaluation
batch_result = jury.evaluate_batch(inputs, metrics)

# Combined analysis
for key in batch_result.results:
    if "Groundedness" in key:
        ground_score = batch_result.results[key].final_score
    if "Hallucination" in key:
        halluc_score = batch_result.results[key].final_score

# Both should indicate quality
quality = ground_score / 5.0  # Normalize to 0-1
consistency = 1 - halluc_score  # Invert (lower hallucination = higher quality)

overall = (quality + consistency) / 2
```

## Customizing Predefined Metrics

### Adjusting Scale

```python
class CustomGroundedness(GroundednessMetric):
    def __init__(self):
        super().__init__()
        # Change to 0-10 scale
        self.scale_min = 0.0
        self.scale_max = 10.0
```

### Modifying Prompt

```python
class StrictGroundedness(GroundednessMetric):
    def get_prompt(self, context=None):
        # Get base prompt
        base_prompt = super().get_prompt(context)
        
        # Add stricter instructions
        return base_prompt + """
        
        IMPORTANT: Be very strict. Any minor unsupported detail
        should result in a score of 2 or below.
        """
```

### Domain-Specific Variant

```python
class MedicalGroundedness(GroundednessMetric):
    def __init__(self):
        super().__init__()
        self.name = "MedicalGroundedness"
        self.description = "Groundedness for medical information"
    
    def get_prompt(self, context=None):
        prompt = super().get_prompt(context)
        return prompt + """
        
        Pay special attention to:
        - Medical terminology accuracy
        - Treatment recommendations
        - Dosage information
        - Safety warnings
        """
```

## Best Practices

### For Groundedness

1. **Always provide source_text** in context
2. **Use with RAG systems** to prevent hallucinations
3. **Set threshold** based on your risk tolerance (e.g., score ≥ 4 = accept)
4. **Inspect low scores** to understand what judges found unsupported

### For Hallucination

1. **Use for general outputs** without specific sources
2. **Combine with fact-checking** for critical applications
3. **Set threshold** conservatively (e.g., score ≤ 0.3 = accept)
4. **Review medium scores** (0.3-0.7) manually

## See Also

- [Metric (Base)](base.md)
- [JuryEvaluator](../core/evaluator.md)
- [Custom Metrics Guide](../../docs/metrics.md)
