# Examples

Real-world examples demonstrating LLM Jury in action.

## RAG System Validation

Validate that retrieval-augmented generation outputs are grounded in source documents.

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Setup evaluation panel
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),
    LLMJudge(ChatAnthropic(model="claude-3-sonnet-20240229"), name="claude"),
]

jury = JuryEvaluator(judges=judges)

# Your RAG system
def rag_pipeline(query):
    # Retrieve documents
    docs = retriever.get_relevant_documents(query)
    context = "\n".join([doc.page_content for doc in docs])
    
    # Generate answer
    answer = llm.generate(query, context)
    
    # Validate with jury
    result = jury.evaluate(
        context={"source_text": context},
        output=answer,
        metric=GroundednessMetric()
    )
    
    # Check quality
    if result.is_valid and result.confidence > 0.7:
        return answer
    else:
        # Regenerate or flag for review
        return regenerate_with_stricter_instructions(query, context)

# Use it
answer = rag_pipeline("What is the capital of France?")
```

## Content Moderation Pipeline

Use multiple judges for sensitive content decisions.

```python
from llm_jury.strategies.consensus import ConsensusStrategy

class ContentModerator:
    def __init__(self):
        # Create diverse panel
        self.judges = [
            LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),
            LLMJudge(ChatAnthropic(model="claude-3-opus-20240229"), name="claude"),
            LLMJudge(ChatGoogleGenerativeAI(model="gemini-1.5-pro"), name="gemini"),
        ]
        
        # Require strong consensus (80%)
        self.jury = JuryEvaluator(
            judges=self.judges,
            strategy=ConsensusStrategy(threshold=0.8)
        )
    
    def is_safe(self, content):
        metric = SafetyMetric()  # Custom metric for safety
        
        result = self.jury.evaluate(
            context={"content": content},
            output=content,
            metric=metric
        )
        
        # Check consensus
        consensus_reached = result.manifest.metadata["consensus_reached"]
        
        if not consensus_reached:
            # Uncertainty - route to human moderator
            return None, "Requires human review"
        
        return result.is_valid, result.manifest.individual_scores

moderator = ContentModerator()
is_safe, details = moderator.is_safe(user_content)

if is_safe is None:
    route_to_human_moderator(user_content)
elif is_safe:
    publish_content(user_content)
else:
    reject_content(user_content, details)
```

## Multi-Metric Evaluation

Evaluate outputs across multiple criteria simultaneously.

```python
from llm_jury.metrics.predefined import GroundednessMetric, HallucinationMetric

# Custom metrics
class RelevanceMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Relevance",
            description="How well the output answers the query",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context=None):
        return "Rate how relevant and on-topic this response is (1-5)..."

# Evaluate on multiple dimensions
metrics = [
    GroundednessMetric(),
    HallucinationMetric(),
    RelevanceMetric()
]

inputs = {
    "response_1": {
        "source_text": retrieved_docs,
        "output": model_output,
        "query": user_query
    }
}

batch_result = jury.evaluate_batch(inputs, metrics)

# Aggregate scores
scores = {
    "groundedness": batch_result.get_score("response_1_Groundedness"),
    "hallucination": batch_result.get_score("response_1_Hallucination"),
    "relevance": batch_result.get_score("response_1_Relevance")
}

# Weighted overall quality
quality = (
    scores["groundedness"] * 0.4 +
    (1 - scores["hallucination"]) * 0.3 +  # Invert hallucination
    scores["relevance"] * 0.3
)

print(f"Overall quality: {quality:.2f}")
```

## Batch Production Evaluation

Evaluate many outputs efficiently.

```python
import pandas as pd

# Load production data
df = pd.read_csv("production_outputs.csv")

# Prepare batch
inputs = {}
for idx, row in df.iterrows():
    inputs[f"output_{idx}"] = {
        "source_text": row["retrieved_context"],
        "output": row["model_output"],
        "query": row["user_query"]
    }

# Evaluate batch
metrics = [GroundednessMetric()]
batch_result = jury.evaluate_batch(inputs, metrics)

# Add results to dataframe
df["jury_score"] = [
    batch_result.results[f"output_{idx}_Groundedness"].final_score
    for idx in range(len(df))
]

df["jury_valid"] = [
    batch_result.results[f"output_{idx}_Groundedness"].is_valid
    for idx in range(len(df))
]

df["jury_confidence"] = [
    batch_result.results[f"output_{idx}_Groundedness"].confidence
    for idx in range(len(df))
]

# Analyze
print(f"Pass rate: {df['jury_valid'].mean():.2%}")
print(f"Average score: {df['jury_score'].mean():.2f}")
print(f"Average confidence: {df['jury_confidence'].mean():.2f}")

# Flag low-confidence results
low_confidence = df[df["jury_confidence"] < 0.5]
print(f"Flagged for review: {len(low_confidence)}")
```

## Weighted Judge Panel

Give more weight to trusted models.

```python
from llm_jury.strategies.weighted import WeightedSum

# Setup panel with different trust levels
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),          # Premium
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5"), # Standard
    LLMJudge(ChatOllama(model="llama3"), name="llama3"),         # Local
]

# Assign weights based on validation accuracy
weights = {
    "gpt-4": 2.0,      # Highest trust
    "gpt-3.5": 1.0,    # Standard
    "llama3": 0.5      # Lower trust but free
}

jury = JuryEvaluator(
    judges=judges,
    strategy=WeightedSum(weights=weights)
)

# Expensive model has more influence
result = jury.evaluate(...)
```

## Agent with Hallucination Shield

Validate agent reasoning steps.

```python
from llm_jury.tools.shield import HallucinationShield
from langchain.agents import AgentExecutor, create_react_agent

# Setup shield
shield_jury = JuryEvaluator(
    judges=[
        LLMJudge(ChatOpenAI(model="gpt-4o"), name="validator-1"),
        LLMJudge(ChatAnthropic(model="claude-3-sonnet-20240229"), name="validator-2"),
    ]
)
shield = HallucinationShield(shield_jury)

# Agent loop with validation
class ValidatedAgent:
    def __init__(self, llm, tools, shield):
        self.llm = llm
        self.tools = tools
        self.shield = shield
        self.context = ""
    
    def step(self, observation):
        # Agent decides next action
        thought = self.llm.generate(f"{self.context}\n{observation}")
        action = self.parse_action(thought)
        
        # Validate before execution
        validation = self.shield.validate_step(
            context_text=self.context,
            proposed_action=action
        )
        
        if validation.is_valid:
            result = self.execute(action)
            self.context += f"\n{action} -> {result}"
            return result
        else:
            # Agent receives feedback
            guidance = self.shield.get_recovery_guidance(validation)
            self.context += f"\nFeedback: {guidance}"
            return self.step(observation)  # Retry

agent = ValidatedAgent(llm, tools, shield)
result = agent.run("Book a flight to Paris")
```

## A/B Testing Strategies

Compare different aggregation approaches.

```python
from llm_jury.strategies.consensus import MajorityVoting
from llm_jury.strategies.weighted import WeightedAverage

test_cases = load_validation_set()

# Strategy A: Majority Voting
jury_a = JuryEvaluator(judges=judges, strategy=MajorityVoting())

# Strategy B: Weighted Average
jury_b = JuryEvaluator(judges=judges, strategy=WeightedAverage())

results_a = []
results_b = []

for case in test_cases:
    result_a = jury_a.evaluate(case["context"], case["output"], metric)
    result_b = jury_b.evaluate(case["context"], case["output"], metric)
    
    results_a.append(result_a.final_score)
    results_b.append(result_b.final_score)

# Compare with ground truth
correlation_a = compute_correlation(results_a, test_cases["labels"])
correlation_b = compute_correlation(results_b, test_cases["labels"])

print(f"Strategy A correlation: {correlation_a:.3f}")
print(f"Strategy B correlation: {correlation_b:.3f}")
```

## Cost-Optimized Pipeline

Balance accuracy and cost.

```python
class TieredEvaluator:
    def __init__(self):
        # Cheap, fast judges
        self.fast_judges = [
            LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="fast-1"),
            LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="fast-2"),
        ]
        
        # Expensive, accurate judges
        self.premium_judges = [
            LLMJudge(ChatOpenAI(model="gpt-4o"), name="premium-1"),
            LLMJudge(ChatAnthropic(model="claude-3-opus-20240229"), name="premium-2"),
        ]
        
        self.fast_jury = JuryEvaluator(judges=self.fast_judges)
        self.premium_jury = JuryEvaluator(judges=self.premium_judges)
    
    def evaluate(self, context, output, metric):
        # Try fast jury first
        fast_result = self.fast_jury.evaluate(context, output, metric)
        
        # If confident, accept result
        if fast_result.confidence > 0.8:
            return fast_result
        
        # Otherwise, use premium jury
        print("Low confidence, using premium jury...")
        return self.premium_jury.evaluate(context, output, metric)

evaluator = TieredEvaluator()
result = evaluator.evaluate(context, output, metric)
```

## Custom Metric Example

Domain-specific evaluation criteria.

```python
class CodeQualityMetric(Metric):
    def __init__(self):
        super().__init__(
            name="CodeQuality",
            description="Evaluates code correctness, style, and efficiency",
            scale_min=1.0,
            scale_max=10.0
        )
    
    def get_prompt(self, context=None):
        code = context.get("output_text", "")
        requirements = context.get("requirements", "")
        
        return f"""
        Evaluate this code on a scale of 1-10:
        
        REQUIREMENTS:
        {requirements}
        
        CODE:
        {code}
        
        CRITERIA:
        10: Perfect - correct, efficient, clean
        7-9: Good - works well, minor improvements
        4-6: Acceptable - works but has issues
        1-3: Poor - major problems or incorrect
        
        Consider:
        - Correctness
        - Code style
        - Efficiency
        - Error handling
        """

# Use it
code_jury = JuryEvaluator(judges=judges)
result = code_jury.evaluate(
    context={
        "requirements": "Write a function to find prime numbers",
        "output_text": generated_code
    },
    output=generated_code,
    metric=CodeQualityMetric()
)

if result.final_score >= 7:
    accept_code(generated_code)
else:
    regenerate_with_feedback(result.manifest.individual_scores)
```

## Next Steps

- Review [API Reference](../api/overview.md) for detailed documentation
- Check [Core Concepts](core-concepts.md) for deeper understanding
- Explore [Architecture](architecture.md) for system design
