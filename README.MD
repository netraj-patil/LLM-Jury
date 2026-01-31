# LLM Jury 🧑‍⚖️

A powerful multi-model LLM evaluation framework with consensus-based aggregation for RAG, summarization, and agentic AI workflows.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Multi-Model Jury System**: Leverage multiple LLMs as judges to evaluate outputs
- **Consensus-Based Aggregation**: Majority voting, weighted strategies, and consensus thresholds
- **Custom Metrics**: Define your own evaluation criteria with flexible prompt templates
- **Hallucination Detection**: Built-in groundedness and hallucination metrics
- **Agentic Shield**: Validate agentic workflows to prevent compounding errors
- **Feature Extraction**: Automatic linguistic and complexity analysis
- **Batch Evaluation**: Process multiple inputs efficiently
- **LangChain Integration**: Works with any LangChain-compatible model

## 📦 Installation

### From GitHub (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/netraj-patil/LLM-Jury.git
cd LLM-Jury

# Install in editable mode
pip install -e .

# Or install with specific LLM providers
pip install -e ".[openai]"      # For OpenAI models
pip install -e ".[anthropic]"   # For Anthropic models
pip install -e ".[google]"      # For Google models
pip install -e ".[all-providers]"  # All providers
```

### From Git URL

```bash
pip install git+https://github.com/netraj-patil/LLM-Jury.git
```

### With Extras

```bash
# Development tools
pip install -e ".[dev]"

# Documentation tools
pip install -e ".[docs]"

# Everything
pip install -e ".[full]"
```

## 🚀 Quick Start

### Basic Evaluation Example

```python
from langchain_openai import ChatOpenAI
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from llm_jury.metrics.predefined import GroundednessMetric
from llm_jury.strategies.consensus import MajorityVoting

# Setup judges
judge_1 = LLMJudge(model=ChatOpenAI(model="gpt-4"), name="GPT-4")
judge_2 = LLMJudge(model=ChatOpenAI(model="gpt-3.5-turbo"), name="GPT-3.5")

# Create jury with majority voting strategy
jury = JuryEvaluator(
    judges=[judge_1, judge_2],
    strategy=MajorityVoting()
)

# Evaluate
context = {
    "source_text": "The Apollo 11 mission landed on the Moon in 1969.",
    "output_text": "Neil Armstrong walked on the Moon in 1969."
}

result = jury.evaluate(
    context=context,
    output=context["output_text"],
    metric=GroundednessMetric()
)

print(f"Score: {result.final_score}")
print(f"Confidence: {result.confidence}")
print(f"Recommendation: {result.get_recommendation()}")
```

## 📚 Core Components

### 1. **Judges**

Judges are the evaluators that score outputs based on metrics.

```python
from llm_jury.judges.llm_judge import LLMJudge
from langchain_anthropic import ChatAnthropic

# Create an LLM judge
claude_judge = LLMJudge(
    model=ChatAnthropic(model="claude-3-sonnet-20240229"),
    name="Claude-3-Sonnet"
)
```

### 2. **Metrics**

Metrics define what to evaluate and how to prompt judges.

#### Predefined Metrics

```python
from llm_jury.metrics.predefined import GroundednessMetric, HallucinationMetric

groundedness = GroundednessMetric()
hallucination = HallucinationMetric()
```

#### Custom Metrics

```python
from llm_jury.metrics.base import Metric

class CompletenessMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Completeness",
            description="Evaluates if summary captures all key points",
            scale_min=1.0,
            scale_max=5.0
        )

    def get_prompt(self, context=None):
        source = context.get("source_text", "")
        output = context.get("output_text", "")

        return f"""
        Evaluate if this summary is complete:

        SOURCE: {source}
        SUMMARY: {output}

        Rate 1-5 where 5 is completely comprehensive.
        """
```

### 3. **Aggregation Strategies**

Strategies combine multiple judge scores into a final verdict.

#### Majority Voting

```python
from llm_jury.strategies.consensus import MajorityVoting

strategy = MajorityVoting()
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

#### Consensus with Threshold

```python
from llm_jury.strategies.consensus import ConsensusStrategy

# Require 70% agreement
strategy = ConsensusStrategy(threshold=0.7)
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

#### Weighted Strategies

```python
from llm_jury.strategies.weighted import WeightedSum

# Trust certain judges more
weights = {
    "GPT-4": 2.0,
    "Claude-3": 1.5,
    "GPT-3.5": 1.0
}

strategy = WeightedSum(weights=weights)
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

#### Simple Average

```python
from llm_jury.strategies.weighted import WeightedAverage

strategy = WeightedAverage()
jury = JuryEvaluator(judges=judges, strategy=strategy)
```

### 4. **Hallucination Shield**

Protect agentic workflows from compounding errors.

```python
from llm_jury.tools.shield import HallucinationShield

# Create shield with configured jury
shield = HallucinationShield(jury_evaluator=jury)

# Validate an agent's proposed action
context = "User's bank balance is $1,234.56"
proposed_action = "Transfer $5,000 to account #9876"

validation = shield.validate_step(
    context_text=context,
    proposed_action=proposed_action
)

if not validation.is_valid:
    guidance = shield.get_recovery_guidance(validation)
    print(guidance)  # Get feedback for the agent
```

## 🎯 Use Cases

### 1. RAG Evaluation

```python
from llm_jury.metrics.predefined import GroundednessMetric

# Evaluate if RAG output is grounded in retrieved context
result = jury.evaluate(
    context={
        "source_text": retrieved_documents,
        "output_text": llm_response
    },
    output=llm_response,
    metric=GroundednessMetric()
)
```

### 2. Summarization Quality

```python
from llm_jury.metrics.base import Metric

# Create custom summarization metrics
completeness = CompletenessMetric()
conciseness = ConcisenessMetric()
coherence = CoherenceMetric()

# Evaluate with multiple metrics
for metric in [completeness, conciseness, coherence]:
    result = jury.evaluate(context, summary, metric)
    print(f"{metric.name}: {result.final_score}")
```

### 3. Batch Evaluation

```python
# Evaluate multiple outputs at once
batch_inputs = {
    "doc_1": {"source_text": "...", "output": "summary 1"},
    "doc_2": {"source_text": "...", "output": "summary 2"},
    "doc_3": {"source_text": "...", "output": "summary 3"}
}

metrics = [GroundednessMetric(), HallucinationMetric()]

batch_result = jury.evaluate_batch(batch_inputs, metrics)

print(f"Overall Quality: {batch_result.overall_quality()}")
for key, result in batch_result.results.items():
    print(f"{key}: {result.final_score}")
```

## 📊 Feature Extraction

The library automatically extracts linguistic features from evaluated text:

```python
result = jury.evaluate(context, output, metric)

features = result.manifest.features
print(f"Word Count: {features['word_count']}")
print(f"Flesch Reading Ease: {features['flesch_reading_ease']}")
print(f"Lexical Diversity: {features['lexical_diversity']}")
print(f"Compression Ratio: {features['compression_ratio']}")
```

Available features:

- **Text Metrics**: Word count, sentence count, character count, paragraph count
- **Complexity**: Flesch Reading Ease, lexical diversity, average sentence length
- **Special Analysis**: Difficult words, modality verbs, Shannon entropy

## 🏗️ Architecture

```
llm_jury/
├── core/              # Core evaluation engine
│   ├── evaluator.py   # JuryEvaluator orchestrator
│   └── manifest.py    # Result structures
├── judges/            # Judge implementations
│   ├── base.py        # Abstract Judge interface
│   └── llm_judge.py   # LangChain LLM judges
├── metrics/           # Evaluation criteria
│   ├── base.py        # Abstract Metric interface
│   └── predefined.py  # Built-in metrics
├── strategies/        # Aggregation logic
│   ├── base.py        # Strategy interface
│   ├── consensus.py   # Voting strategies
│   └── weighted.py    # Weighted strategies
├── features/          # Feature extraction
│   └── extractor.py   # Text analysis
└── tools/             # Agentic integration
    └── shield.py      # Hallucination Shield
```

## 🔧 Advanced Configuration

### Dynamic Strategy Switching

```python
jury = JuryEvaluator(judges=judges, strategy=MajorityVoting())

# Switch to consensus for critical evaluations
jury.set_strategy(ConsensusStrategy(threshold=0.8))

# Add more judges on the fly
jury.add_judge(new_judge)
```

### Custom Judge Implementation

```python
from llm_jury.judges.base import Judge
from llm_jury.core.manifest import JudgeScore

class CustomHeuristicJudge(Judge):
    def __init__(self):
        super().__init__(name="heuristic-1")

    def evaluate_score(self, prompt, context):
        # Your custom logic here
        score = custom_evaluation_function(context)

        return JudgeScore(
            score=score,
            reasoning="Custom heuristic evaluation",
            judge_id=self.name
        )
```

## 📖 Examples

Check out the `examples/` directory for complete use cases:

- **`summarization_examples.py`**: 5 comprehensive summarization scenarios
- Custom metrics creation
- All aggregation strategies
- Batch processing
- Hallucination detection

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Inspired by research in multi-model consensus and LLM-as-a-judge paradigms

## 📧 Contact

**Netraj Patil** - [@netraj-patil](https://github.com/netraj-patil)

Project Link: [https://github.com/netraj-patil/LLM-Jury](https://github.com/netraj-patil/LLM-Jury)

## 🗺️ Roadmap

- [ ] Add semantic embedding features (PCA, cosine similarity)
- [ ] Implement composite metrics for multi-dimensional evaluation
- [ ] Support for custom reliability models (XGBoost, Random Forest)
- [ ] Add visualization tools for jury analysis
- [ ] Expand predefined metric library
- [ ] Add streaming evaluation support
- [ ] Create web UI for interactive evaluation

---

**Star ⭐ this repository if you find it useful!**
