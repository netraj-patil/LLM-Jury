# Getting Started

This guide will help you set up and use LLM Jury in your projects.

## Installation

Install LLM Jury using pip:

```bash
pip install llm-jury
```

### Dependencies

LLM Jury requires Python 3.8+ and depends on:

- `langchain-core`: For LLM integrations
- Standard library modules for text analysis

Optional dependencies for specific models:

```bash
# OpenAI models
pip install langchain-openai

# Anthropic models
pip install langchain-anthropic

# Google models
pip install langchain-google-genai
```

## Basic Usage

### 1. Create Judges

Judges are the evaluators in your panel. You can use any LangChain-compatible model:

```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Create judges from different model providers
judge_gpt4 = LLMJudge(
    model=ChatOpenAI(model="gpt-4o"),
    name="gpt-4o"
)

judge_claude = LLMJudge(
    model=ChatAnthropic(model="claude-3-sonnet-20240229"),
    name="claude-3-sonnet"
)
```

### 2. Initialize the Evaluator

The `JuryEvaluator` orchestrates the evaluation process:

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.strategies.consensus import MajorityVoting

jury = JuryEvaluator(
    judges=[judge_gpt4, judge_claude],
    strategy=MajorityVoting()  # Default aggregation strategy
)
```

### 3. Choose a Metric

Metrics define what you're evaluating:

```python
from llm_jury.metrics.predefined import GroundednessMetric

metric = GroundednessMetric()
```

### 4. Evaluate

Run the evaluation:

```python
result = jury.evaluate(
    context={
        "source_text": "The Eiffel Tower is located in Paris, France.",
        "output_text": "The Eiffel Tower is in Paris."
    },
    output="The Eiffel Tower is in Paris.",
    metric=metric
)

# Access results
print(f"Final Score: {result.final_score}")
print(f"Is Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")
print(f"Recommendation: {result.get_recommendation()}")
```

## Complete Example

Here's a full example evaluating a RAG system output:

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric
from llm_jury.strategies.consensus import MajorityVoting
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Setup judges
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4o"),
    LLMJudge(ChatAnthropic(model="claude-3-sonnet-20240229"), name="claude"),
]

# Create evaluator
jury = JuryEvaluator(judges=judges, strategy=MajorityVoting())

# Prepare evaluation context
retrieved_docs = """
The Python programming language was created by Guido van Rossum 
and first released in 1991. Python emphasizes code readability 
with significant whitespace.
"""

model_output = """
Python was created by Guido van Rossum in 1991. It's known for 
its clean syntax and readability.
"""

# Evaluate
result = jury.evaluate(
    context={"source_text": retrieved_docs},
    output=model_output,
    metric=GroundednessMetric()
)

# Display results
print(f"✓ Score: {result.final_score}/5.0")
print(f"✓ Valid: {result.is_valid}")
print(f"✓ Confidence: {result.confidence:.2%}")

# Inspect individual judge scores
for score in result.manifest.individual_scores:
    print(f"\n{score.judge_id}: {score.score}")
    print(f"Reasoning: {score.reasoning}")
```

## Batch Evaluation

Evaluate multiple outputs at once:

```python
inputs = {
    "item1": {
        "source": "Context for item 1...",
        "output": "Generated text 1..."
    },
    "item2": {
        "source": "Context for item 2...",
        "output": "Generated text 2..."
    }
}

metrics = [GroundednessMetric(), HallucinationMetric()]

batch_result = jury.evaluate_batch(inputs=inputs, metrics=metrics)

# Access individual results
for key, result in batch_result.results.items():
    print(f"{key}: {result.final_score}")
```

## Next Steps

- Learn about [Core Concepts](core-concepts.md)
- Explore [Aggregation Strategies](strategies.md)
- See [Examples](examples.md) for real-world use cases
- Check the [API Reference](../api/overview.md) for detailed documentation
