# LLM Jury 🎯

A robust framework for evaluating Large Language Model outputs using multi-model consensus and systematic quality assessment.

## Overview

LLM Jury implements a "jury of models" approach to evaluate AI-generated content. Instead of relying on a single judge, it orchestrates multiple LLMs to score outputs against defined metrics, then aggregates their verdicts for reliable, transparent evaluation.

**Key Features:**

- **Multi-Model Consensus**: Use multiple LLMs as judges to reduce bias and improve reliability
- **Flexible Metrics**: Built-in metrics for groundedness, hallucination detection, plus custom metric support
- **Aggregation Strategies**: Majority voting, consensus thresholds, weighted scoring
- **Feature Extraction**: Automatic text analysis (readability, complexity, linguistic features)
- **Hallucination Shield**: Validate agentic workflows to prevent error propagation
- **Full Audit Trails**: Complete manifests with individual scores, reasoning, and metadata

## Quick Start

### Installation

```bash
pip install llm-jury
```

### Basic Usage

```python
from langchain_openai import ChatOpenAI
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric
from llm_jury.strategies.consensus import MajorityVoting

# Create a panel of judges
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4"), name="gpt-4"),
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5"),
]

# Initialize the jury with a strategy
jury = JuryEvaluator(judges=judges, strategy=MajorityVoting())

# Evaluate an output
result = jury.evaluate(
    context={"source_text": "The capital of France is Paris."},
    output="Paris is the capital of France, located in Europe.",
    metric=GroundednessMetric()
)

print(f"Score: {result.final_score}")
print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      JuryEvaluator                          │
│  Orchestrates evaluation workflow and aggregation           │
└────────────┬─────────────────────────────┬──────────────────┘
             │                             │
      ┌──────▼──────┐              ┌──────▼──────┐
      │   Judges    │              │   Metrics   │
      │  (Models)   │              │  (Criteria) │
      └──────┬──────┘              └──────┬──────┘
             │                             │
      ┌──────▼──────────────────────────────▼──────┐
      │         Aggregation Strategy                │
      │  (MajorityVoting, Consensus, Weighted)      │
      └──────┬──────────────────────────────────────┘
             │
      ┌──────▼──────┐
      │   Manifest  │
      │ (Audit Trail)│
      └─────────────┘
```

## Core Components

### 1. Judges
Evaluate content based on prompts. Support for:
- LLM-based judges (OpenAI, Anthropic, Google, etc. via LangChain)
- Custom function-based judges
- Ensemble combinations

### 2. Metrics
Define evaluation criteria:
- **GroundednessMetric**: Verifies claims against source context
- **HallucinationMetric**: Detects fabricated information
- **Custom Metrics**: Create domain-specific evaluations

### 3. Aggregation Strategies
Combine multiple judge scores:
- **MajorityVoting**: Select most common score
- **ConsensusStrategy**: Require threshold agreement
- **WeightedSum**: Trust some judges more than others

### 4. Feature Extraction
Automatic analysis of text:
- Basic stats (word count, sentence count)
- Readability (Flesch score, lexical diversity)
- Complexity (syllable counts, entropy)

### 5. Hallucination Shield
Validate agentic workflows step-by-step to prevent compounding errors.

## Use Cases

### RAG Systems
Validate that generated answers are grounded in retrieved documents.

```python
from llm_jury.metrics.predefined import GroundednessMetric

result = jury.evaluate(
    context={"source_text": retrieved_docs, "output_text": llm_answer},
    output=llm_answer,
    metric=GroundednessMetric()
)
```

### Content Moderation
Ensure generated content meets quality and safety standards.

```python
from llm_jury.metrics.custom import CustomMetric

class ToneMetric(CustomMetric):
    # Define professional tone evaluation
    pass

result = jury.evaluate(context={}, output=text, metric=ToneMetric())
```

### Agentic AI
Validate agent actions before execution to prevent hallucination propagation.

```python
from llm_jury.tools.shield import HallucinationShield

shield = HallucinationShield(jury_evaluator=jury)
validation = shield.validate_step(
    context_text=current_state,
    proposed_action=agent_action
)

if validation.is_valid:
    execute_action()
else:
    retry_with_guidance(validation.consensus_reasoning)
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Core Concepts](docs/core-concepts.md)
- [API Reference](docs/api-reference.md)
- [Custom Metrics Guide](docs/custom-metrics.md)
- [Aggregation Strategies](docs/aggregation-strategies.md)
- [Examples](examples/)

## Examples

Check the `examples/` directory for complete implementations:

- **RAG Evaluation**: Validate retrieval-augmented generation systems
- **Summarization Quality**: Multi-dimensional summary assessment
- **Agentic Shield**: Prevent hallucinations in multi-step workflows
- **Custom Metrics**: Domain-specific evaluation criteria

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use LLM Jury in your research, please cite:

```bibtex
@software{llm_jury,
  title = {LLM Jury: Multi-Model Consensus for LLM Evaluation},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/llm-jury}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/llm-jury/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llm-jury/discussions)
- **Documentation**: [Full Docs](https://llm-jury.readthedocs.io)

---

Built with reliability and transparency in mind.
