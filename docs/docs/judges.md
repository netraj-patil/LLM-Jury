# Judges

Judges are the evaluators that score LLM outputs. Each judge represents an independent evaluation perspective.

## Overview

A judge receives an evaluation prompt and context, then returns a structured score with reasoning. LLM Jury supports multiple types of judges that can work together.

## LLM Judge

The primary judge implementation uses LangChain models to evaluate text.

### Basic Usage

```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI

judge = LLMJudge(
    model=ChatOpenAI(model="gpt-4o", temperature=0),
    name="gpt-4o"
)
```

### Supported Models

Any LangChain-compatible model:

```python
# OpenAI
from langchain_openai import ChatOpenAI
judge_gpt = LLMJudge(ChatOpenAI(model="gpt-4o"))

# Anthropic
from langchain_anthropic import ChatAnthropic
judge_claude = LLMJudge(ChatAnthropic(model="claude-3-opus-20240229"))

# Google
from langchain_google_genai import ChatGoogleGenerativeAI
judge_gemini = LLMJudge(ChatGoogleGenerativeAI(model="gemini-1.5-pro"))

# Local models via Ollama
from langchain_ollama import ChatOllama
judge_local = LLMJudge(ChatOllama(model="llama3"))
```

### How It Works

1. **Prompt Construction**: Combines metric instructions with context
2. **Model Invocation**: Calls the LLM via LangChain
3. **Response Parsing**: Extracts score and reasoning using regex/JSON
4. **Score Packaging**: Returns a `JudgeScore` object

### Expected Output Format

LLMJudge expects models to respond in this format:

```
Score: 4.0
Reasoning: The output is well-grounded in the source text with only minor paraphrasing.
Metrics: {"accuracy": 0.9, "completeness": 0.85}
```

The parsing is flexible and will extract what's available.

## Creating Custom Judges

Implement the `Judge` abstract base class:

```python
from llm_jury.judges.base import Judge
from llm_jury.core.manifest import JudgeScore

class HeuristicJudge(Judge):
    """A rule-based judge that checks word count."""
    
    def __init__(self, name="word-counter"):
        super().__init__(name)
        
    def evaluate_score(self, prompt, context):
        # Extract output text
        output = context.get("output_text", "")
        
        # Simple heuristic: score based on length
        word_count = len(output.split())
        
        if word_count < 10:
            score = 1.0
            reason = "Output too short"
        elif word_count < 50:
            score = 3.0
            reason = "Acceptable length"
        else:
            score = 5.0
            reason = "Good detail level"
            
        return JudgeScore(
            score=score,
            reasoning=reason,
            judge_id=self.name
        )
```

### Custom Judge with External API

```python
import requests

class CustomAPIJudge(Judge):
    def __init__(self, api_endpoint, api_key):
        super().__init__(name="custom-api")
        self.endpoint = api_endpoint
        self.api_key = api_key
        
    def evaluate_score(self, prompt, context):
        response = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"prompt": prompt, "context": context}
        )
        
        data = response.json()
        
        return JudgeScore(
            score=data["score"],
            reasoning=data["explanation"],
            judge_id=self.name,
            metrics_metadata=data.get("details", {})
        )
```

## Judge Selection Strategy

### Diversity

Choose judges from different model families:

```python
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),
    LLMJudge(ChatAnthropic(model="claude-3-sonnet-20240229"), name="claude"),
    LLMJudge(ChatGoogleGenerativeAI(model="gemini-1.5-pro"), name="gemini"),
]
```

**Benefits**: Different training data, architectures, and biases

### Specialization

Mix general and specialized judges:

```python
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="general"),
    HeuristicJudge(name="length-check"),
    ToxicityJudge(name="safety"),
]
```

### Cost Optimization

Balance expensive and cheap models:

```python
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="premium"),  # Expensive, accurate
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="fast"),  # Cheap, fast
    LLMJudge(ChatOllama(model="llama3"), name="local"),  # Free, local
]
```

## Judge Configuration

### Temperature

Control creativity vs consistency:

```python
# More deterministic (recommended for evaluation)
judge_strict = LLMJudge(
    ChatOpenAI(model="gpt-4o", temperature=0)
)

# More varied
judge_creative = LLMJudge(
    ChatOpenAI(model="gpt-4o", temperature=0.7)
)
```

### Model Parameters

```python
judge = LLMJudge(
    ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=500,  # Limit response length
        timeout=30,      # API timeout
    ),
    name="gpt-4-strict"
)
```

## Error Handling

Judges that fail don't crash the entire jury:

```python
# If one judge fails, others continue
try:
    score = judge.evaluate_score(prompt, context)
except Exception as e:
    # Logged but evaluation continues with other judges
    print(f"Judge {judge.name} failed: {e}")
```

### Creating Fallback Judges

```python
class RobustJudge(Judge):
    def evaluate_score(self, prompt, context):
        try:
            # Primary evaluation logic
            return self._evaluate_with_api(prompt, context)
        except Exception as e:
            # Fallback to heuristic
            return self._fallback_evaluation(context)
```

## Performance Tips

### Parallel Execution

Judges run in parallel automatically:

```python
# All 5 judges run concurrently
jury = JuryEvaluator(judges=[judge1, judge2, judge3, judge4, judge5])
```

### Caching

Cache judge responses for repeated evaluations:

```python
from functools import lru_cache

class CachedJudge(Judge):
    @lru_cache(maxsize=1000)
    def evaluate_score(self, prompt, context):
        # Expensive evaluation
        return super().evaluate_score(prompt, context)
```

## Best Practices

1. **Use 3-5 judges** for most scenarios
2. **Mix model providers** for diversity
3. **Set temperature=0** for consistency
4. **Name judges clearly** for manifest readability
5. **Test judges independently** before combining
6. **Monitor costs** for API-based judges

## Judge Metadata

Access judge information from results:

```python
result = jury.evaluate(...)

for score in result.manifest.individual_scores:
    print(f"Judge: {score.judge_id}")
    print(f"Score: {score.score}")
    print(f"Reasoning: {score.reasoning}")
    print(f"Metadata: {score.metrics_metadata}")
```

## Next Steps

- Learn about [Metrics](metrics.md) that judges evaluate
- Explore [Aggregation Strategies](strategies.md) for combining judge scores
- See [Examples](examples.md) of judge configurations
