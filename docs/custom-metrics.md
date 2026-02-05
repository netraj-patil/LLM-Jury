# Custom Metrics Guide

Learn how to create domain-specific evaluation metrics for your use case.

## Table of Contents

- [When to Create Custom Metrics](#when-to-create-custom-metrics)
- [Metric Anatomy](#metric-anatomy)
- [Step-by-Step Guide](#step-by-step-guide)
- [Examples by Domain](#examples-by-domain)
- [Prompt Engineering Tips](#prompt-engineering-tips)
- [Testing Your Metrics](#testing-your-metrics)
- [Best Practices](#best-practices)

---

## When to Create Custom Metrics

Create custom metrics when:

- **Domain-specific quality**: Medical accuracy, legal precision, technical correctness
- **Brand requirements**: Tone, style, voice alignment
- **Compliance needs**: Regulatory language, required disclaimers
- **User experience**: Clarity, helpfulness, empathy
- **Special criteria**: Code quality, data formatting, structure validation

Built-in metrics (Groundedness, Hallucination) are general-purpose. Custom metrics encode your specific expertise.

---

## Metric Anatomy

Every metric inherits from the `Metric` base class:

```python
from llm_jury.metrics.base import Metric
from typing import Any

class YourMetric(Metric):
    def __init__(self):
        super().__init__(
            name="MetricName",
            description="Brief description",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context: Any = None) -> str:
        # Return evaluation instructions for judges
        pass
```

### Required Components

1. **`__init__()`**: Configure name, description, and scale
2. **`get_prompt()`**: Generate evaluation instructions (the only required method)

### Inherited Components

These are handled automatically:
- **`normalize()`**: Converts scores to [0, 1] range
- **`aggregate_metrics()`**: Combines sub-metric scores

---

## Step-by-Step Guide

### Step 1: Define Your Criteria

Before writing code, clearly define:
- **What are you measuring?** (e.g., professional tone, technical accuracy)
- **What's good vs bad?** (specific examples)
- **What scale makes sense?** (1-5, 0-1, binary)

**Example Criteria - Professional Tone**:
- Formal language (no slang)
- Emotional restraint (not overly emotional)
- Respectful phrasing (courteous)
- Clear communication (unambiguous)

### Step 2: Choose Your Scale

Common scales:

| Scale | Use Case | Example |
|-------|----------|---------|
| 1-5 | Star ratings, quality levels | 5=Excellent, 1=Poor |
| 0-1 | Probabilities, binary detection | 0=No issue, 1=Issue detected |
| 0-10 | Fine-grained scoring | 10=Perfect, 0=Terrible |
| Binary | Pass/fail checks | 1=Pass, 0=Fail |

### Step 3: Write the Prompt Template

Structure your prompt with clear sections:

```python
def get_prompt(self, context: Any = None) -> str:
    output = context.get("output_text", "") if isinstance(context, dict) else ""
    
    return f"""
You are a [ROLE] Evaluator. [Brief role description].

--- TEXT TO EVALUATE ---
{output}

--- EVALUATION CRITERIA ---
1. [Criterion 1]: [What to check]
2. [Criterion 2]: [What to check]
3. [Criterion 3]: [What to check]

--- SCORING GUIDE ---
5 = [Best case]
4 = [Good case]
3 = [Acceptable case]
2 = [Poor case]
1 = [Worst case]

[Additional instructions or warnings]

Score: <number>
Reasoning: <explanation>
"""
```

### Step 4: Implement the Class

```python
class ProfessionalToneMetric(Metric):
    def __init__(self):
        super().__init__(
            name="ProfessionalTone",
            description="Evaluates business-appropriate language",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context: Any = None) -> str:
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
You are a Professional Tone Evaluator. Assess whether the text maintains 
an appropriate professional tone for business communication.

--- TEXT TO EVALUATE ---
{output}

--- EVALUATION CRITERIA ---
1. Language formality (avoids slang, casual expressions)
2. Emotional restraint (measured, not overly emotional)
3. Respectful phrasing (courteous, non-confrontational)
4. Clear communication (concise, unambiguous)
5. Appropriate vocabulary (business-suitable words)

--- SCORING GUIDE ---
5 = Exemplary professional tone throughout
4 = Mostly professional with minor lapses
3 = Mixed tone, some unprofessional elements
2 = Largely unprofessional tone
1 = Completely inappropriate for business context

Score: <number>
Reasoning: <explanation>
"""
```

### Step 5: Test It

```python
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI

# Setup
metric = ProfessionalToneMetric()
judge = LLMJudge(ChatOpenAI(model="gpt-4"), name="gpt-4")
jury = JuryEvaluator(judges=[judge])

# Test with professional text
result1 = jury.evaluate(
    context={},
    output="We appreciate your feedback and will address this promptly.",
    metric=metric
)
print(f"Professional text score: {result1.final_score}")

# Test with unprofessional text
result2 = jury.evaluate(
    context={},
    output="Yeah whatever dude, we'll get to it when we feel like it lol",
    metric=metric
)
print(f"Unprofessional text score: {result2.final_score}")
```

---

## Examples by Domain

### Medical Accuracy

```python
class MedicalAccuracyMetric(Metric):
    def __init__(self):
        super().__init__(
            name="MedicalAccuracy",
            description="Evaluates medical information for accuracy and safety",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context: Any = None) -> str:
        output = context.get("output_text", "")
        source = context.get("source_text", "")
        
        return f"""
You are a Medical Accuracy Evaluator. Assess the medical information for 
factual accuracy, appropriate caution, and safety.

--- REFERENCE MEDICAL LITERATURE ---
{source}

--- MEDICAL CONTENT TO EVALUATE ---
{output}

--- EVALUATION CRITERIA ---
1. Factual Accuracy: Claims align with medical literature
2. Appropriate Disclaimers: Includes "consult a doctor" where needed
3. Safety Concerns: No dangerous recommendations
4. Terminology: Correct use of medical terms
5. Evidence Level: Strength of claims matches evidence

--- SCORING GUIDE ---
5 = Medically accurate, appropriately cautious, safe
4 = Mostly accurate with minor imprecisions
3 = Some inaccuracies or missing disclaimers
2 = Significant inaccuracies or safety concerns
1 = Dangerous or completely inaccurate information

CRITICAL: Score 1 if content could cause harm.

Score: <number>
Reasoning: <explanation with specific examples>
Metrics: {{"accuracy": <0-5>, "safety": <0-5>, "disclaimers": <0-5>}}
"""
```

### Code Quality

```python
class CodeQualityMetric(Metric):
    def __init__(self):
        super().__init__(
            name="CodeQuality",
            description="Evaluates code for correctness, style, and best practices",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context: Any = None) -> str:
        code = context.get("output_text", "")
        language = context.get("language", "Python")
        
        return f"""
You are a Code Quality Evaluator specializing in {language}.

--- CODE TO EVALUATE ---
```{language.lower()}
{code}
```

--- EVALUATION CRITERIA ---
1. Correctness: Code accomplishes the intended task
2. Best Practices: Follows language conventions and idioms
3. Readability: Clear naming, proper structure, comments where needed
4. Efficiency: No obvious performance issues
5. Security: No vulnerabilities (SQL injection, XSS, etc.)

--- SCORING GUIDE ---
5 = Production-ready, exemplary code
4 = Good code with minor improvements possible
3 = Functional but needs refactoring
2 = Works but has significant issues
1 = Broken or severely flawed

Score: <number>
Reasoning: <specific issues or strengths>
Metrics: {{"correctness": <0-5>, "style": <0-5>, "security": <0-5>}}
"""
```

### Legal Compliance

```python
class LegalComplianceMetric(Metric):
    def __init__(self, requirements: List[str]):
        super().__init__(
            name="LegalCompliance",
            description="Binary compliance check for legal requirements",
            scale_min=0.0,
            scale_max=1.0
        )
        self.requirements = requirements
    
    def get_prompt(self, context: Any = None) -> str:
        output = context.get("output_text", "")
        
        requirements_text = "\n".join([
            f"   {i+1}. {req}" for i, req in enumerate(self.requirements)
        ])
        
        return f"""
You are a Legal Compliance Auditor. Check if the text meets ALL required 
compliance criteria. This is a binary pass/fail check.

--- TEXT TO AUDIT ---
{output}

--- REQUIRED COMPLIANCE CRITERIA ---
{requirements_text}

--- SCORING ---
1.0 = ALL requirements met (fully compliant)
0.0 = ANY requirement missing (non-compliant)

This is binary. If even one requirement is missing, score MUST be 0.0.

Score: <0.0 or 1.0>
Reasoning: <list which requirements are met or missing>
"""

# Usage
financial_compliance = LegalComplianceMetric(
    requirements=[
        "Includes risk disclosure statement",
        "States past performance doesn't guarantee future results",
        "Advises consulting a financial advisor",
        "Clearly labeled as not financial advice"
    ]
)
```

### Customer Service Quality

```python
class CustomerServiceMetric(Metric):
    def __init__(self):
        super().__init__(
            name="CustomerServiceQuality",
            description="Evaluates customer service response quality",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context: Any = None) -> str:
        customer_query = context.get("input_prompt", "")
        response = context.get("output_text", "")
        
        return f"""
You are a Customer Service Quality Evaluator.

--- CUSTOMER QUERY ---
{customer_query}

--- AGENT RESPONSE ---
{response}

--- EVALUATION CRITERIA ---
1. Empathy: Acknowledges customer's situation/feelings
2. Clarity: Easy to understand, no jargon
3. Completeness: Fully addresses the query
4. Helpfulness: Provides actionable next steps
5. Professionalism: Polite, patient, respectful

--- SCORING GUIDE ---
5 = Exceptional service, customer likely very satisfied
4 = Good response, minor improvements possible
3 = Adequate but missing some elements
2 = Poor response, customer likely unsatisfied
1 = Unacceptable (rude, unhelpful, or wrong information)

Score: <number>
Reasoning: <specific strengths and weaknesses>
"""
```

---

## Prompt Engineering Tips

### 1. Be Specific

**Bad**: "Evaluate the quality of this text"

**Good**: "Evaluate whether this text maintains a professional tone by checking: (1) formal language, (2) emotional restraint, (3) respectful phrasing"

### 2. Provide Clear Anchors

Define what each score means with concrete examples:

```
5 = All safety disclaimers present (e.g., "Consult your doctor")
4 = Most disclaimers present, missing minor ones
3 = Some critical disclaimers missing
...
```

### 3. Use Examples in Prompts

```python
f"""
--- GOOD EXAMPLES ---
Example 1: "According to the study, X was found..."  (Cites source)
Example 2: "The data shows..."  (References data)

--- BAD EXAMPLES ---
Example 1: "Everyone knows that X..."  (No evidence)
Example 2: "I think X probably..."  (Speculation)

Now evaluate the following text...
"""
```

### 4. Handle Edge Cases

Explicitly address what to do with:
- Very short texts
- Missing context
- Ambiguous content

```python
f"""
NOTE: If the text is too short to evaluate (<10 words), score as 3 (neutral).
If critical context is missing, note this in your reasoning.
"""
```

### 5. Request Structured Output

```python
f"""
Provide your response in this exact format:
Score: <number between 1-5>
Reasoning: <2-3 sentence explanation>
Metrics: {{"criterion_1": <score>, "criterion_2": <score>}}
"""
```

### 6. Calibrate Strictness

Be explicit about how strict the evaluation should be:

**Lenient**: "Give benefit of the doubt. Minor issues are acceptable."

**Strict**: "Be critical. Only near-perfect content should score 5."

**Balanced**: "Apply standards you'd expect in professional production."

---

## Testing Your Metrics

### 1. Create Test Cases

```python
test_cases = [
    {
        "name": "Clearly professional",
        "text": "We appreciate your inquiry and will respond within 24 hours.",
        "expected_range": (4.0, 5.0)
    },
    {
        "name": "Clearly unprofessional",
        "text": "lol whatever dude chill out",
        "expected_range": (1.0, 2.0)
    },
    {
        "name": "Borderline",
        "text": "Thanks for reaching out! We'll get back to you soon.",
        "expected_range": (3.0, 4.0)
    }
]
```

### 2. Run Evaluations

```python
for case in test_cases:
    result = jury.evaluate(
        context={},
        output=case["text"],
        metric=your_metric
    )
    
    in_range = case["expected_range"][0] <= result.final_score <= case["expected_range"][1]
    status = "PASS" if in_range else "FAIL"
    
    print(f"{status}: {case['name']}")
    print(f"  Score: {result.final_score} (expected {case['expected_range']})")
    print(f"  Reasoning: {result.manifest.individual_scores[0].reasoning[:100]}...")
```

### 3. Check Inter-Judge Agreement

```python
# Use multiple judges
jury = JuryEvaluator(judges=[judge1, judge2, judge3])

result = jury.evaluate(...)

print(f"Confidence (agreement): {result.confidence}")
print("Individual scores:", [s.score for s in result.manifest.individual_scores])

# Low confidence might indicate prompt ambiguity
if result.confidence < 0.5:
    print("WARNING: Low agreement - consider clarifying prompt")
```

### 4. Validate Against Human Judgment

```python
human_scores = [4.5, 3.8, 4.2, 5.0, 2.1]  # From human evaluators
llm_scores = []

for text in test_texts:
    result = jury.evaluate(context={}, output=text, metric=your_metric)
    llm_scores.append(result.final_score)

# Calculate correlation
from scipy.stats import pearsonr
correlation, p_value = pearsonr(human_scores, llm_scores)
print(f"Correlation with human judgment: {correlation:.2f}")
```

---

## Best Practices

### Do's

- **Start simple**: Begin with clear, binary criteria before adding complexity
- **Test extensively**: Try edge cases, ambiguous examples, obvious cases
- **Iterate on prompts**: Refine based on unexpected judge behavior
- **Use multiple judges**: Reduces impact of individual model quirks
- **Document thoroughly**: Explain what the metric measures and when to use it
- **Provide examples**: Include sample evaluations in docstrings

### Don'ts

- **Don't over-specify**: Too many criteria dilute focus
- **Don't use subjective language**: "Good", "bad" without definition
- **Don't mix concerns**: One metric = one aspect (separate "accuracy" from "tone")
- **Don't ignore scale consistency**: Keep similar metrics on similar scales
- **Don't skip validation**: Always test before production use

### Scale Selection Guidelines

| Your Need | Recommended Scale | Reason |
|-----------|-------------------|--------|
| Quality levels | 1-5 | Intuitive star rating |
| Detection (yes/no) | 0-1 | Binary probability |
| Compliance | 0-1 | Pass/fail clarity |
| Fine-grained ranking | 0-10 | More granularity |
| Multiple aspects | 1-5 per aspect | Sub-metrics in metadata |

### Common Pitfalls

**Pitfall 1: Vague criteria**
```python
# BAD
"Evaluate the quality of this text"

# GOOD
"Evaluate whether claims are supported by citations (score 5 if all claims cited)"
```

**Pitfall 2: Inconsistent scales**
```python
# BAD - Mixing scales
class MyMetric:
    # Uses 1-5 in prompt but 0-100 in scale_max
    
# GOOD - Consistent
class MyMetric:
    # Prompt says "1-5", scale_min=1.0, scale_max=5.0
```

**Pitfall 3: Ignoring context structure**
```python
# BAD
output = context  # Assumes context is a string

# GOOD
output = context.get("output_text", "") if isinstance(context, dict) else str(context)
```

---

## Advanced: Multi-Aspect Metrics

For complex evaluations, use the `metrics_metadata` field:

```python
class ComprehensiveQualityMetric(Metric):
    def get_prompt(self, context=None):
        return f"""
        Evaluate on 3 dimensions:
        
        Score: <overall 1-5>
        Reasoning: <explanation>
        Metrics: {{
            "clarity": <1-5>,
            "accuracy": <1-5>,
            "completeness": <1-5>
        }}
        """

# Access sub-scores
result = jury.evaluate(...)
sub_scores = result.manifest.individual_scores[0].metrics_metadata
print(f"Clarity: {sub_scores.get('clarity')}")
```

---

## Template

Copy and customize this template:

```python
from llm_jury.metrics.base import Metric
from typing import Any

class MyCustomMetric(Metric):
    """
    [Description of what this metric evaluates]
    
    Use case: [When to use this metric]
    
    Examples:
        >>> metric = MyCustomMetric()
        >>> result = jury.evaluate(context={}, output="...", metric=metric)
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the metric.
        
        Args:
            **kwargs: Custom configuration options
        """
        super().__init__(
            name="MyMetricName",
            description="Short description for logs",
            scale_min=1.0,
            scale_max=5.0
        )
        self.custom_param = kwargs.get('custom_param', 'default')
    
    def get_prompt(self, context: Any = None) -> str:
        """
        Generate evaluation prompt.
        
        Args:
            context: Dict with keys:
                - output_text: Text to evaluate (required)
                - source_text: Reference material (optional)
                - [custom keys as needed]
        """
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return f"""
You are a [Role] Evaluator. [Brief role description].

--- CONTENT TO EVALUATE ---
{output}

--- EVALUATION CRITERIA ---
1. [Criterion 1]: [What to check]
2. [Criterion 2]: [What to check]

--- SCORING GUIDE ---
5 = [Best case]
4 = [Good case]
3 = [Acceptable case]
2 = [Poor case]
1 = [Worst case]

Score: <number>
Reasoning: <explanation>
"""
```

---

## Next Steps

- Check out [examples/custom_metrics/](../examples/custom_metrics/) for more examples
- Read [API Reference](api-reference.md) for complete `Metric` class documentation
- See [Aggregation Strategies](aggregation-strategies.md) for combining metrics
- Join discussions on best practices in the community forums
