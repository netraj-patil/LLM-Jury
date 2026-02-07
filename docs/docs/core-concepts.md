# Core Concepts

Understanding the key components of LLM Jury will help you use the library effectively.

## The Four Pillars

LLM Jury is built on four core components that work together:

```
┌─────────────────────────────────────────────────┐
│              JuryEvaluator                      │
│  (Orchestrates the evaluation process)          │
└───────┬─────────────────────────────────────────┘
        │
        ├──> Judges (Who evaluates?)
        ├──> Metrics (What to evaluate?)
        ├──> Strategies (How to aggregate?)
        └──> Manifest (What happened?)
```

## 1. Judges

**Judges** are the evaluators that score outputs. Each judge is an independent model or function.

### Types of Judges

- **LLM Judges**: Use language models (GPT-4, Claude, etc.) via LangChain
- **Heuristic Judges**: Use rule-based logic or traditional NLP
- **Custom Judges**: Implement your own evaluation logic

### Why Multiple Judges?

- **Reduce Bias**: Different models have different strengths and weaknesses
- **Increase Reliability**: Consensus is more trustworthy than a single opinion
- **Capture Nuance**: Some judges excel at detecting specific issues

```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI

judge = LLMJudge(
    model=ChatOpenAI(model="gpt-4o"),
    name="gpt-4o"
)
```

## 2. Metrics

**Metrics** define *what* is being evaluated. They generate the prompts that judges use.

### Built-in Metrics

- **GroundednessMetric**: Checks if output is supported by source context
- **HallucinationMetric**: Detects fabricated or inconsistent information

### Metric Components

```python
class Metric:
    name: str              # Identifier (e.g., "Groundedness")
    description: str       # What it measures
    scale_min: float       # Minimum score (e.g., 1.0)
    scale_max: float       # Maximum score (e.g., 5.0)
    
    def get_prompt(context) -> str:
        # Returns evaluation instructions
    
    def normalize(score) -> float:
        # Converts to [0, 1] range
```

### Custom Metrics

Create your own evaluation criteria:

```python
from llm_jury.metrics.base import Metric

class CoherenceMetric(Metric):
    """
    Evaluates the logical flow, structural organization, and clarity of the model's output.
    Ensures that ideas connect smoothly, transitions are natural, and the text is not 
    disjointed or rambling.
    """

    def __init__(self):
        super().__init__(
            name="Coherence", 
            description="Measures the logical flow, consistency, and structural organization of the text.",
            scale_min=1.0,
            scale_max=5.0
        )

    def get_prompt(self, context: Any = None) -> str:
        """
        Generates a prompt asking the judge to evaluate the structural quality of the text.
        
        Expected context structure (Dict):
        - output_text: The model's generated answer to check.
        - input_prompt: The original user question (optional, for context).
        """
        # Safe extraction of strings if context is a dict
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        user_input = context.get("input_prompt", "") if isinstance(context, dict) else ""
        
        # We include User Input for context, though Coherence is largely intrinsic to the Output.
        return (
            "You are a Coherence Judge. Your task is to evaluate the 'Model Output' based on its "
            "logical flow, structural organization, and clarity. Ignore factual accuracy; focus "
            "strictly on how well the text is written and organized.\n\n"
            "--- USER INPUT (For Context) ---\n"
            f"{user_input}\n\n"
            "--- MODEL OUTPUT ---\n"
            f"{output}\n\n"
            "--- SCORING CRITERIA ---\n"
            "5: Excellent. Ideas flow logically with clear transitions. The structure is intuitive and easy to follow.\n"
            "4: Good. The text is organized and clear, with only minor issues in transitions or flow.\n"
            "3: Acceptable. The text is understandable but may feel choppy, repetitive, or slightly disjointed.\n"
            "2: Poor. Hard to follow. Sentences or paragraphs often lack connection or logical progression.\n"
            "1: Incoherent. The text is rambling, nonsensical, or completely lacks structure.\n\n"
            "Provide your verdict as a score between 1 and 5."
        )
```

## 3. Aggregation Strategies

**Strategies** combine multiple judge scores into a single verdict.

### Available Strategies

#### Majority Voting
Democratic approach - the most common score wins.

```python
from llm_jury.strategies.consensus import MajorityVoting

strategy = MajorityVoting()
```

**Use when**: You want equal weight for all judges and prefer discrete scores.

#### Weighted Sum
Assign different importance to each judge.

```python
from llm_jury.strategies.weighted import WeightedSum

strategy = WeightedSum(weights={
    "gpt-4o": 1.5,      # Higher weight
    "claude": 1.0,
    "llama": 0.5        # Lower weight
})
```

**Use when**: Some judges are more reliable for your specific task.

#### Consensus Strategy
Requires a threshold of agreement (e.g., 70% must agree).

```python
from llm_jury.strategies.consensus import ConsensusStrategy

strategy = ConsensusStrategy(threshold=0.7)
```

**Use when**: You need high confidence in decisions.

#### Weighted Average
Simple arithmetic mean with variance-based confidence.

```python
from llm_jury.strategies.weighted import WeightedAverage

strategy = WeightedAverage()
```

**Use when**: You want continuous scores and standard statistical measures.

## 4. Evaluation Results

### EvaluationResult

The output of every evaluation:

```python
@dataclass
class EvaluationResult:
    final_score: float       # Aggregated score
    is_valid: bool          # Pass/fail based on threshold
    confidence: float       # Inter-judge agreement (0-1)
    manifest: JuryManifest  # Full audit trail
```

### JuryManifest

A comprehensive record of the evaluation:

```python
@dataclass
class JuryManifest:
    individual_scores: List[JudgeScore]  # Each judge's verdict
    features: Dict[str, Any]             # Extracted text features
    metadata: Dict[str, Any]             # Strategy info, timestamps
    timestamp: datetime                  # When it happened
```

### Accessing Details

```python
result = jury.evaluate(...)

# High-level results
print(result.final_score)
print(result.is_valid)
print(result.confidence)

# Individual judge scores
for score in result.manifest.individual_scores:
    print(f"{score.judge_id}: {score.score}")
    print(f"Reasoning: {score.reasoning}")

# Text features
print(result.manifest.features["word_count"])
print(result.manifest.features["flesch_reading_ease"])

# Get recommendation
print(result.get_recommendation())
```

## Evaluation Workflow

Here's how everything comes together:

```
1. Input arrives
   ├─ Context (source documents)
   └─ Output (text to evaluate)

2. Feature Extraction
   └─ Analyze text metrics (complexity, length, etc.)

3. Prompt Generation
   └─ Metric creates evaluation instructions

4. Parallel Judging
   ├─ Judge 1 scores → JudgeScore
   ├─ Judge 2 scores → JudgeScore
   └─ Judge N scores → JudgeScore

5. Score Normalization
   └─ Convert all scores to [0, 1] range

6. Aggregation
   └─ Strategy combines scores → AggregationResult

7. Manifest Creation
   └─ Package everything → EvaluationResult
```

## Best Practices

### Choosing Judges

- Use **3-5 judges** for most cases (more = slower but more reliable)
- Mix **different model families** (OpenAI, Anthropic, Google)
- Consider **model capabilities** (some excel at reasoning, others at factuality)

### Selecting Metrics

- Use **Groundedness** for RAG systems
- Use **Hallucination** for general text generation
- Create **custom metrics** for domain-specific evaluation

### Strategy Selection

- Start with **MajorityVoting** for simplicity
- Use **WeightedSum** when you have trust levels
- Use **ConsensusStrategy** for high-stakes decisions

### Performance Tips

- Judges run in **parallel** by default (via ThreadPoolExecutor)
- Use **batch evaluation** for multiple items
- Cache results when evaluating the same content repeatedly

## Next Steps

- Explore [Judges](judges.md) in detail
- Learn about [Metrics](metrics.md)
- Understand [Aggregation Strategies](strategies.md)
- See the [Architecture](architecture.md) overview
