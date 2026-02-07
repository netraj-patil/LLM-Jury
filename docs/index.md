# LLM Jury

**Multi-Model Consensus Evaluation Framework for Large Language Models**

LLM Jury is a powerful Python library that orchestrates multiple AI judges to evaluate LLM outputs with enhanced reliability and transparency. By combining judgments from diverse models through sophisticated aggregation strategies, it reduces bias and provides comprehensive audit trails for every evaluation.

## Why LLM Jury?

Traditional single-model evaluation suffers from inherent biases and blind spots. LLM Jury solves this by:

- **Multi-Judge Consensus**: Leverage multiple models (GPT-4, Claude, Gemini, etc.) to evaluate outputs
- **Flexible Aggregation**: Choose from voting, weighted averages, or consensus strategies
- **Full Transparency**: Every evaluation includes a detailed manifest with individual scores and reasoning
- **Hallucination Prevention**: Built-in shield for agentic workflows to catch compounding errors
- **Production-Ready**: Designed for RAG systems, content moderation, and quality assurance

## Quick Start

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Create a diverse panel of judges
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4o"),
    LLMJudge(ChatAnthropic(model="claude-3-sonnet"), name="claude-3-sonnet"),
]

# Initialize the evaluator
jury = JuryEvaluator(judges=judges)

# Evaluate output against retrieved context
result = jury.evaluate(
    context={"source_text": "Paris is the capital of France."},
    output="The capital of France is Paris.",
    metric=GroundednessMetric()
)

print(f"Score: {result.final_score}")
print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")
```

## Key Features

### Comprehensive Metrics
- **Groundedness**: Verify claims against source documents
- **Hallucination Detection**: Identify fabricated information
- **Custom Metrics**: Define your own evaluation criteria

### Flexible Aggregation
- **Majority Voting**: Democratic consensus
- **Weighted Strategies**: Trust certain models more
- **Consensus Thresholds**: Require strong agreement

### Rich Analytics
- **Feature Extraction**: Automatic text complexity analysis
- **Audit Trails**: Complete manifest of evaluation process
- **Batch Processing**: Evaluate multiple outputs efficiently

### Hallucination Shield
A specialized tool for agentic workflows that validates each reasoning step before execution, preventing error cascades.

## Installation

```bash
pip install llm-jury
```

For development:

```bash
git clone https://github.com/netraj-patil/LLM-Jury.git
cd LLM-Jury
pip install -e ".[dev]"
```

## Use Cases

- **RAG System Validation**: Ensure generated answers are grounded in retrieved documents
- **Content Moderation**: Multi-model review for sensitive content decisions
- **Quality Assurance**: Automated evaluation of production LLM outputs
- **Research**: Compare model performance with statistical rigor
- **Agentic AI**: Validate reasoning chains and tool calls

## Project Status

LLM Jury is actively developed and production-ready. We follow semantic versioning and maintain comprehensive test coverage.

## Documentation Structure

- **[Docs](docs/getting-started.md)**: Guides, concepts, and tutorials
- **[API Reference](api/overview.md)**: Detailed class and method documentation

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please see our contributing guidelines for more information.
