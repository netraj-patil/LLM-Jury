# Judge (Base)

Abstract base class for all judge implementations.

## Class Definition

```python
from abc import ABC, abstractmethod

class Judge(ABC):
    def __init__(self, name: str)
```

## Constructor

### Parameters

- **name** (`str`): Unique identifier for this judge (e.g., "gpt-4o", "heuristic-1")

## Abstract Methods

### evaluate_score

```python
@abstractmethod
def evaluate_score(self, prompt: str, context: Any) -> JudgeScore
```

Evaluates the provided prompt and context to produce a score.

#### Parameters

- **prompt** (`str`): Evaluation instruction or criteria (e.g., "Rate groundedness 1-5")
- **context** (`Any`): Content to evaluate
  - Can be a string (raw text)
  - Can be a dictionary with keys like `source`, `output`, `retrieval_context`

#### Returns

`JudgeScore`: Structured object containing:
- `score`: Numerical evaluation
- `reasoning`: Textual justification
- `judge_id`: This judge's identifier
- `metrics_metadata`: Optional sub-metrics

#### Responsibilities

1. Invoke judgment logic (LLM API call or local function)
2. Parse the output (extract JSON, regex matches, etc.)
3. Return structured JudgeScore

## Attributes

### name

```python
self.name: str
```

The unique identifier for this judge.

## Implementing Custom Judges

### Basic Example

```python
from llm_jury.judges.base import Judge
from llm_jury.core.manifest import JudgeScore

class SimpleJudge(Judge):
    def __init__(self, name="simple"):
        super().__init__(name)
    
    def evaluate_score(self, prompt, context):
        # Your evaluation logic here
        output = context.get("output_text", "")
        
        # Simple scoring based on length
        word_count = len(output.split())
        score = min(5.0, word_count / 20)  # Max 5.0
        
        return JudgeScore(
            score=score,
            reasoning=f"Scored based on length: {word_count} words",
            judge_id=self.name
        )
```

### Heuristic Judge

```python
class ReadabilityJudge(Judge):
    def __init__(self):
        super().__init__(name="readability-judge")
    
    def evaluate_score(self, prompt, context):
        from llm_jury.features.extractor import FeatureExtractor
        
        output = context.get("output_text", "")
        extractor = FeatureExtractor()
        
        features = extractor.extract_complexity(output)
        flesch_score = features["flesch_reading_ease"]
        
        # Convert Flesch (0-100) to 1-5 scale
        # 90-100 → 5, 60-70 → 3, 0-30 → 1
        if flesch_score >= 80:
            score = 5.0
        elif flesch_score >= 60:
            score = 4.0
        elif flesch_score >= 40:
            score = 3.0
        elif flesch_score >= 20:
            score = 2.0
        else:
            score = 1.0
        
        return JudgeScore(
            score=score,
            reasoning=f"Flesch Reading Ease: {flesch_score:.1f}",
            judge_id=self.name,
            metrics_metadata={"flesch_score": flesch_score}
        )
```

### External API Judge

```python
import requests

class CustomAPIJudge(Judge):
    def __init__(self, api_endpoint, api_key, name="custom-api"):
        super().__init__(name)
        self.endpoint = api_endpoint
        self.api_key = api_key
    
    def evaluate_score(self, prompt, context):
        try:
            response = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "prompt": prompt,
                    "context": context
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return JudgeScore(
                score=data["score"],
                reasoning=data.get("explanation", ""),
                judge_id=self.name,
                metrics_metadata=data.get("details", {})
            )
        except Exception as e:
            # Return error score
            return JudgeScore(
                score=0.0,
                reasoning=f"API call failed: {str(e)}",
                judge_id=self.name
            )
```

### Cached Judge

```python
from functools import lru_cache

class CachedJudge(Judge):
    def __init__(self, base_judge):
        super().__init__(name=f"cached-{base_judge.name}")
        self.base_judge = base_judge
    
    @lru_cache(maxsize=1000)
    def _cached_evaluate(self, prompt, context_str):
        # Convert context to string for caching
        context_dict = eval(context_str)  # In production, use proper serialization
        return self.base_judge.evaluate_score(prompt, context_dict)
    
    def evaluate_score(self, prompt, context):
        # Serialize context for cache key
        context_str = str(context)
        return self._cached_evaluate(prompt, context_str)
```

## Error Handling

Judges should handle errors gracefully:

```python
class RobustJudge(Judge):
    def evaluate_score(self, prompt, context):
        try:
            # Primary evaluation logic
            return self._evaluate_with_api(prompt, context)
        except TimeoutError:
            return JudgeScore(
                score=0.0,
                reasoning="Evaluation timed out",
                judge_id=self.name
            )
        except Exception as e:
            return JudgeScore(
                score=0.0,
                reasoning=f"Evaluation failed: {str(e)}",
                judge_id=self.name
            )
```

## Best Practices

1. **Always set judge_id** correctly in returned JudgeScore
2. **Provide meaningful reasoning** for transparency
3. **Handle errors gracefully** without crashing
4. **Use consistent scale** (1-5 or 0-1)
5. **Return quickly** (use timeouts for API calls)
6. **Add metadata** for additional context

## String Representation

```python
judge = SimpleJudge(name="my-judge")
print(judge)  # <SimpleJudge(name='my-judge')>
```

## See Also

- [LLMJudge](llm_judge.md) - Concrete implementation using LangChain
- [JudgeScore](../core/manifest.md#judgescore)
- [JuryEvaluator](../core/evaluator.md)
