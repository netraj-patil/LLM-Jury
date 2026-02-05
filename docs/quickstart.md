# Quickstart Guide

Get started with LLM Jury in 5 minutes.

## Installation

```bash
pip install llm-jury langchain-openai
```

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

## Your First Evaluation

```python
from langchain_openai import ChatOpenAI
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric

# Step 1: Create judges
judge1 = LLMJudge(ChatOpenAI(model="gpt-4"), name="gpt-4")
judge2 = LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5")

# Step 2: Create jury
jury = JuryEvaluator(judges=[judge1, judge2])

# Step 3: Evaluate
result = jury.evaluate(
    context={
        "source_text": "The Eiffel Tower is in Paris, France.",
        "output_text": "The Eiffel Tower is located in Paris."
    },
    output="The Eiffel Tower is located in Paris.",
    metric=GroundednessMetric()
)

# Step 4: Check results
print(f"Score: {result.final_score}")
print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")
print(f"Recommendation: {result.get_recommendation()}")
```

## Common Use Cases

### 1. RAG System Validation

```python
from llm_jury.metrics.predefined import GroundednessMetric

# Your RAG pipeline
retrieved_docs = retriever.get_relevant_documents(query)
llm_answer = llm.invoke(query, context=retrieved_docs)

# Validate groundedness
result = jury.evaluate(
    context={"source_text": retrieved_docs, "output_text": llm_answer},
    output=llm_answer,
    metric=GroundednessMetric()
)

if result.is_valid:
    return llm_answer
else:
    return "I cannot provide a grounded answer based on the available context."
```

### 2. Content Quality Check

```python
from llm_jury.metrics.base import Metric

class ToneMetric(Metric):
    def __init__(self):
        super().__init__(
            name="ProfessionalTone",
            description="Checks professional tone",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context=None):
        output = context.get("output_text", "")
        return f"""
Rate the professionalism of this text (1-5):
{output}

Score: <number>
Reasoning: <explanation>
"""

# Use it
result = jury.evaluate(
    context={},
    output="We appreciate your feedback and will respond promptly.",
    metric=ToneMetric()
)
```

### 3. Batch Evaluation

```python
# Evaluate multiple outputs at once
inputs = {
    "answer1": {
        "output": "Paris is the capital of France.",
        "source": "France's capital city is Paris."
    },
    "answer2": {
        "output": "London is in the UK.",
        "source": "The United Kingdom's capital is London."
    }
}

results = jury.evaluate_batch(
    inputs=inputs,
    metrics=[GroundednessMetric()]
)

# Check results
for key, result in results.results.items():
    print(f"{key}: {result.final_score}")
```

## Configuration Options

### Using Different Models

```python
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

judges = [
    LLMJudge(ChatOpenAI(model="gpt-4"), name="gpt-4"),
    LLMJudge(ChatAnthropic(model="claude-3-opus-20240229"), name="claude"),
    LLMJudge(ChatGoogleGenerativeAI(model="gemini-pro"), name="gemini")
]

jury = JuryEvaluator(judges=judges)
```

### Choosing an Aggregation Strategy

```python
from llm_jury.strategies.consensus import MajorityVoting, ConsensusStrategy
from llm_jury.strategies.weighted import WeightedSum

# Option 1: Majority voting (default)
jury = JuryEvaluator(judges=[...], strategy=MajorityVoting())

# Option 2: Require strong consensus
jury = JuryEvaluator(judges=[...], strategy=ConsensusStrategy(threshold=0.8))

# Option 3: Weight some judges more
jury = JuryEvaluator(
    judges=[...],
    strategy=WeightedSum({"gpt-4": 1.0, "gpt-3.5": 0.5})
)
```

## Debugging

### Inspect Individual Scores

```python
result = jury.evaluate(...)

for score in result.manifest.individual_scores:
    print(f"\n{score.judge_id}:")
    print(f"  Score: {score.score}")
    print(f"  Reasoning: {score.reasoning}")
```

### Check Text Features

```python
features = result.manifest.features
print(f"Word count: {features['word_count']}")
print(f"Readability: {features['flesch_reading_ease']}")
```

### View Aggregation Details

```python
metadata = result.manifest.metadata
print(f"Strategy: {metadata['strategy_used']}")
print(f"Vote distribution: {metadata['aggregation_metadata']}")
```

## Best Practices

1. **Start with 3-5 judges** - Balance between speed and reliability
2. **Use diverse models** - Different providers reduce correlated errors
3. **Check confidence scores** - Low confidence indicates edge cases
4. **Test your metrics** - Validate on known good/bad examples
5. **Monitor costs** - Use cheaper models for most judges, one premium model

## Error Handling

```python
result = jury.evaluate(...)

# Check if evaluation succeeded
if result.is_valid and result.confidence > 0.7:
    # High confidence, use result
    use_result(result.final_score)
elif result.confidence < 0.5:
    # Low confidence, flag for review
    flag_for_human_review(result)
else:
    # Acceptable but not ideal
    use_with_caution(result)
```

## Next Steps

- **[Core Concepts](core-concepts.md)** - Understand how LLM Jury works
- **[Custom Metrics](custom-metrics.md)** - Build domain-specific evaluations
- **[API Reference](api-reference.md)** - Complete method documentation
- **[Examples](../examples/)** - Real-world implementations

## Common Issues

### Issue: Inconsistent scores between runs

**Cause**: LLM temperature too high

**Solution**: 
```python
judge = LLMJudge(
    ChatOpenAI(model="gpt-4", temperature=0.0),  # Deterministic
    name="gpt-4"
)
```

### Issue: Slow evaluations

**Cause**: Sequential judge execution

**Solution**: Already parallelized! Reduce judge count or use faster models:
```python
judges = [
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name=f"judge-{i}")
    for i in range(3)  # Use 3 fast models instead of 5
]
```

### Issue: High API costs

**Solution**: Mix premium and budget models:
```python
from llm_jury.strategies.weighted import WeightedSum

judges = [
    LLMJudge(ChatOpenAI(model="gpt-4"), name="gpt-4"),           # 1 premium
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5-1"),  # 2 budget
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5-2")
]

jury = JuryEvaluator(
    judges=judges,
    strategy=WeightedSum({"gpt-4": 0.6, "gpt-3.5-1": 0.2, "gpt-3.5-2": 0.2})
)
```

## Support

- **Documentation**: [https://llm-jury.readthedocs.io](https://llm-jury.readthedocs.io)
- **GitHub Issues**: [https://github.com/yourusername/llm-jury/issues](https://github.com/yourusername/llm-jury/issues)
- **Discord**: [Join our community](https://discord.gg/llm-jury)

---

Happy evaluating!
