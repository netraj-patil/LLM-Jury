# LLMJudge

Concrete Judge implementation that uses LangChain models for evaluation.

## Class Definition

```python
from langchain_core.language_models import BaseChatModel, BaseLanguageModel

class LLMJudge(Judge):
    def __init__(
        self,
        model: Union[BaseChatModel, BaseLanguageModel],
        name: Optional[str] = None
    )
```

## Constructor

### Parameters

- **model** (`Union[BaseChatModel, BaseLanguageModel]`): LangChain model instance
  - Examples: `ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, `ChatOllama`
- **name** (`Optional[str]`): Custom name for the judge
  - If None, defaults to model's class name or model identifier

### Example

```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# OpenAI model
judge_gpt = LLMJudge(
    model=ChatOpenAI(model="gpt-4o", temperature=0),
    name="gpt-4o"
)

# Anthropic model
judge_claude = LLMJudge(
    model=ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0),
    name="claude-3-sonnet"
)

# Google model
judge_gemini = LLMJudge(
    model=ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
)

# Local model via Ollama
from langchain_ollama import ChatOllama
judge_local = LLMJudge(
    model=ChatOllama(model="llama3"),
    name="llama3-local"
)
```

## Methods

### evaluate_score

```python
def evaluate_score(self, prompt: str, context: Any) -> JudgeScore
```

Executes evaluation using the LangChain model.

#### Parameters

- **prompt** (`str`): Metric evaluation prompt
- **context** (`Any`): Content to evaluate (string or dict)

#### Returns

`JudgeScore`: Structured score with reasoning and metadata

#### Process

1. **Format Context**: Converts context to readable string
2. **Construct Messages**: Creates chat messages for the LLM
3. **Invoke Model**: Calls LangChain model
4. **Parse Output**: Extracts score, reasoning, and metadata using regex/JSON
5. **Return JudgeScore**: Packages results

#### Example

```python
judge = LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4")

prompt = "Rate the groundedness of this text on a scale of 1-5..."
context = {
    "source_text": "Paris is the capital of France.",
    "output_text": "The capital of France is Paris."
}

score = judge.evaluate_score(prompt, context)

print(f"Score: {score.score}")
print(f"Reasoning: {score.reasoning}")
print(f"Judge: {score.judge_id}")
```

## Output Format

LLMJudge expects models to respond in this format:

```
Score: 4.5
Reasoning: The output is well-grounded in the source text with minor paraphrasing.
Metrics: {"accuracy": 0.9, "completeness": 0.85}
```

### Parsing Logic

The judge uses regex to extract:

- **Score**: Matches `Score: <number>`
- **Reasoning**: Captures text after `Reasoning:`
- **Metrics**: Parses JSON after `Metrics:`

```python
# Score extraction
score_match = re.search(r"Score:\s*([-+]?\d*\.\d+|\d+)", raw_text, re.IGNORECASE)

# Reasoning extraction
reasoning_match = re.search(r"Reasoning:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)

# Metrics extraction (JSON)
json_match = re.search(r"Metrics:\s*(\{.*?\})", raw_text, re.DOTALL)
```

## Error Handling

### API Failures

If the model call fails, returns error score:

```python
JudgeScore(
    score=0.0,
    reasoning="SYSTEM ERROR: Failed to generate evaluation. {error_msg}",
    judge_id=self.name
)
```

### Parsing Failures

If output format is unexpected:
- Score defaults to 0.0
- Reasoning falls back to full raw text
- Metadata remains empty

## Supported Models

### OpenAI

```python
from langchain_openai import ChatOpenAI

judge = LLMJudge(
    ChatOpenAI(
        model="gpt-4o",
        temperature=0,          # Deterministic
        max_tokens=500,         # Limit response length
        timeout=30,             # API timeout
    ),
    name="gpt-4o"
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic

judge = LLMJudge(
    ChatAnthropic(
        model="claude-3-opus-20240229",
        temperature=0,
        max_tokens=500,
    ),
    name="claude-3-opus"
)
```

### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI

judge = LLMJudge(
    ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
    ),
    name="gemini-1.5-pro"
)
```

### Local Models (Ollama)

```python
from langchain_ollama import ChatOllama

judge = LLMJudge(
    ChatOllama(
        model="llama3",
        temperature=0,
    ),
    name="llama3"
)
```

## Configuration Recommendations

### For Evaluation Tasks

```python
# Recommended settings
judge = LLMJudge(
    ChatOpenAI(
        model="gpt-4o",
        temperature=0,      # Deterministic (important!)
        max_tokens=500,     # Sufficient for score + reasoning
        timeout=30,         # Reasonable timeout
    )
)
```

### Temperature

- **0**: Deterministic, consistent (recommended)
- **0.3-0.5**: Slight variation
- **0.7+**: More creative, less consistent

### Max Tokens

- **200-500**: Sufficient for most evaluations
- **1000+**: For detailed reasoning

## Context Formatting

The judge automatically formats complex contexts:

```python
# String context
context = "Some text to evaluate"
# Formatted as-is

# Dict context
context = {
    "source_text": "...",
    "output_text": "...",
    "user_query": "..."
}
# Formatted as:
# SOURCE_TEXT:
# ...
# OUTPUT_TEXT:
# ...
# USER_QUERY:
# ...
```

## Prompt Template

The final prompt sent to the model:

```
{metric_prompt}

--- CONTEXT TO EVALUATE ---
{formatted_context}

--- OUTPUT FORMAT ---
Return your response in the following format:
Score: <float>
Reasoning: <text explanation>
Metrics: <JSON dictionary of sub-metrics if applicable>
```

## Attributes

### model

```python
self.model: Union[BaseChatModel, BaseLanguageModel]
```

The underlying LangChain model instance.

### name

```python
self.name: str
```

The judge's identifier (inherited from Judge base class).

## Best Practices

1. **Set temperature=0** for consistent evaluation
2. **Use appropriate max_tokens** (200-500 typically sufficient)
3. **Set timeouts** to prevent hanging
4. **Test prompts** with your specific models
5. **Monitor costs** for API-based models
6. **Use caching** for repeated evaluations

## Performance

### Latency

- API-based: 100-1000ms per call (varies by provider)
- Local models: Depends on hardware

### Cost

Costs accumulate per evaluation:
- GPT-4o: ~$0.01-0.05 per evaluation
- GPT-3.5: ~$0.001-0.005 per evaluation
- Claude: ~$0.01-0.05 per evaluation
- Local models: Free

## See Also

- [Judge (Base)](base.md)
- [JudgeScore](../core/manifest.md#judgescore)
- [JuryEvaluator](../core/evaluator.md)
