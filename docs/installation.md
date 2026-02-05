# Installation Guide

## Requirements

- Python 3.8 or higher
- pip package manager

## Basic Installation

### Install from PyPI

```bash
pip install llm-jury
```

### Install from Source

```bash
git clone https://github.com/yourusername/llm-jury.git
cd llm-jury
pip install -e .
```

---

## LLM Provider Setup

LLM Jury uses LangChain for model integration. You'll need API keys for your chosen providers.

### OpenAI

```bash
pip install langchain-openai
```

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."

from langchain_openai import ChatOpenAI
from llm_jury.judges.llm_judge import LLMJudge

judge = LLMJudge(
    model=ChatOpenAI(model="gpt-4"),
    name="gpt-4"
)
```

### Anthropic (Claude)

```bash
pip install langchain-anthropic
```

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

from langchain_anthropic import ChatAnthropic
from llm_jury.judges.llm_judge import LLMJudge

judge = LLMJudge(
    model=ChatAnthropic(model="claude-3-opus-20240229"),
    name="claude-opus"
)
```

### Google (Gemini)

```bash
pip install langchain-google-genai
```

```python
import os
os.environ["GOOGLE_API_KEY"] = "..."

from langchain_google_genai import ChatGoogleGenerativeAI
from llm_jury.judges.llm_judge import LLMJudge

judge = LLMJudge(
    model=ChatGoogleGenerativeAI(model="gemini-pro"),
    name="gemini-pro"
)
```

### Groq

```bash
pip install langchain-groq
```

```python
import os
os.environ["GROQ_API_KEY"] = "gsk_..."

from langchain_groq import ChatGroq
from llm_jury.judges.llm_judge import LLMJudge

judge = LLMJudge(
    model=ChatGroq(model="llama-3.1-70b-versatile"),
    name="llama-3.1-70b"
)
```

### Local Models (Ollama)

```bash
# Install Ollama from https://ollama.ai
# Pull a model: ollama pull llama2

pip install langchain-community
```

```python
from langchain_community.llms import Ollama
from llm_jury.judges.llm_judge import LLMJudge

judge = LLMJudge(
    model=Ollama(model="llama2"),
    name="llama2-local"
)
```

---

## Optional Dependencies

### For Agentic Shield with LangGraph

```bash
pip install langgraph
```

### For Advanced Text Analysis

```bash
pip install scipy  # For correlation analysis
pip install pandas  # For batch analysis
```

---

## Verify Installation

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.metrics.predefined import GroundednessMetric
from llm_jury.strategies.consensus import MajorityVoting

print("Installation successful!")
```

---

## Development Setup

For contributing to LLM Jury:

```bash
# Clone repository
git clone https://github.com/yourusername/llm-jury.git
cd llm-jury

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linter
flake8 src/

# Format code
black src/
```

---

## Troubleshooting

### Issue: Import errors

**Solution**: Ensure you've installed the package and its dependencies:
```bash
pip install llm-jury
pip list | grep llm-jury
```

### Issue: API key errors

**Solution**: Verify environment variables are set:
```python
import os
print(os.getenv("OPENAI_API_KEY"))  # Should not be None
```

### Issue: Model not found

**Solution**: Check LangChain provider installation:
```bash
pip install langchain-openai  # Or appropriate provider
```

### Issue: Rate limiting

**Solution**: Reduce concurrent judges or add delays:
```python
import time

# Add rate limiting between evaluations
for item in items:
    result = jury.evaluate(...)
    time.sleep(1)  # 1 second delay
```

---

## Next Steps

- [Quick Start Tutorial](../README.md#quick-start)
- [Core Concepts](core-concepts.md)
- [API Reference](api-reference.md)
- [Examples](../examples/)
