# Feature Extraction

The FeatureExtractor analyzes text to provide quantitative insights into LLM outputs. These features are automatically included in evaluation manifests.

## Overview

Every evaluation automatically extracts features from the output text:

- **Text Metrics**: Basic structural properties
- **Complexity**: Readability and sophistication
- **Special Words**: Linguistic markers and patterns

These features provide context for evaluation results and enable advanced analysis.

## Automatic Extraction

Features are extracted automatically during evaluation:

```python
result = jury.evaluate(
    context={"source_text": "..."},
    output="Your LLM output here...",
    metric=GroundednessMetric()
)

# Access extracted features
features = result.manifest.features

print(features["word_count"])
print(features["flesch_reading_ease"])
print(features["compression_ratio"])
```

## Feature Categories

### Text Metrics

Basic structural properties of the text.

```python
{
    "char_count": 1234,        # Total characters
    "word_count": 250,          # Total words
    "sentence_count": 15,       # Number of sentences
    "paragraph_count": 3,       # Number of paragraphs
    "compression_ratio": 0.68   # Zlib compression ratio
}
```

**Compression Ratio**: Measures information density
- Lower (0.3-0.5): Simple, repetitive text
- Medium (0.5-0.7): Normal prose
- Higher (0.7-0.9): Dense, technical content

### Complexity Metrics

Linguistic sophistication measures.

```python
{
    "flesch_reading_ease": 65.2,    # 0-100 (higher = easier)
    "lexical_diversity": 0.73,       # Type-Token Ratio (0-1)
    "avg_sentence_length": 16.7      # Words per sentence
}
```

**Flesch Reading Ease**:
- 90-100: Very easy (5th grade)
- 60-70: Standard (8th-9th grade)
- 30-50: Difficult (college)
- 0-30: Very difficult (professional)

**Lexical Diversity** (Type-Token Ratio):
- Higher = more varied vocabulary
- Lower = repetitive word use

### Special Words

Linguistic markers and patterns.

```python
{
    "difficult_word_count": 12,     # Words with 3+ syllables
    "modality_verb_count": 5,       # can, should, might, etc.
    "shannon_entropy": 4.23         # Information entropy
}
```

**Shannon Entropy**: Unpredictability of word sequences
- Higher = more diverse/complex
- Lower = repetitive/predictable

## Using Feature Extractor Directly

You can extract features independently:

```python
from llm_jury.features.extractor import FeatureExtractor

extractor = FeatureExtractor()

# Extract all features
text = "Your text here..."
text_features = extractor.extract_text_metrics(text)
complexity = extractor.extract_complexity(text)
special = extractor.extract_special_words(text)

# Combine
all_features = {**text_features, **complexity, **special}
```

## Analyzing Features

### Correlation with Quality

Compare features across good vs bad outputs:

```python
good_outputs = [...]
bad_outputs = [...]

def analyze_features(outputs):
    features = []
    for output in outputs:
        f = extractor.extract_text_metrics(output)
        c = extractor.extract_complexity(output)
        features.append({**f, **c})
    return features

good_features = analyze_features(good_outputs)
bad_features = analyze_features(bad_outputs)

# Compare averages
avg_good_flesch = sum(f["flesch_reading_ease"] for f in good_features) / len(good_features)
avg_bad_flesch = sum(f["flesch_reading_ease"] for f in bad_features) / len(bad_features)
```

### Feature-Based Filtering

Use features for pre-filtering:

```python
def should_evaluate(text):
    features = extractor.extract_text_metrics(text)
    
    # Skip extremely short outputs
    if features["word_count"] < 10:
        return False
    
    # Skip extremely long outputs
    if features["word_count"] > 1000:
        return False
    
    return True

if should_evaluate(output):
    result = jury.evaluate(...)
```

### Batch Feature Extraction

Analyze multiple texts efficiently:

```python
texts = ["Text 1...", "Text 2...", "Text 3..."]

all_features = []
for text in texts:
    features = {
        **extractor.extract_text_metrics(text),
        **extractor.extract_complexity(text),
        **extractor.extract_special_words(text)
    }
    all_features.append(features)

# Analyze patterns
import pandas as pd
df = pd.DataFrame(all_features)
print(df.describe())
```

## Use Cases

### Quality Monitoring

Track feature trends over time:

```python
# Daily production monitoring
daily_outputs = get_outputs_for_today()
daily_features = [
    extractor.extract_complexity(output) 
    for output in daily_outputs
]

avg_readability = sum(f["flesch_reading_ease"] for f in daily_features) / len(daily_features)

if avg_readability < 30:
    alert("Outputs becoming too complex!")
```

### A/B Testing

Compare models on feature distributions:

```python
model_a_outputs = [...]
model_b_outputs = [...]

def avg_complexity(outputs):
    complexities = [
        extractor.extract_complexity(o)["flesch_reading_ease"] 
        for o in outputs
    ]
    return sum(complexities) / len(complexities)

print(f"Model A readability: {avg_complexity(model_a_outputs)}")
print(f"Model B readability: {avg_complexity(model_b_outputs)}")
```

### Anomaly Detection

Detect unusual outputs:

```python
def is_anomalous(text, baseline_features):
    features = extractor.extract_text_metrics(text)
    
    # Check for extreme values
    if features["compression_ratio"] < 0.3:
        return True, "Unusually repetitive"
    
    if features["word_count"] > 2 * baseline_features["avg_word_count"]:
        return True, "Unusually long"
    
    return False, "Normal"
```

## Feature Interpretation

### Compression Ratio Insights

```python
ratio = features["compression_ratio"]

if ratio < 0.4:
    interpretation = "Highly repetitive or simple"
elif ratio < 0.6:
    interpretation = "Normal prose"
elif ratio < 0.8:
    interpretation = "Dense, information-rich"
else:
    interpretation = "Very complex or technical"
```

### Readability Guidelines

```python
flesch = features["flesch_reading_ease"]

if flesch > 80:
    level = "Elementary school"
    action = "Consider adding sophistication"
elif flesch > 60:
    level = "Middle school (ideal for most content)"
    action = "Good readability"
elif flesch > 30:
    level = "College level"
    action = "May be too complex for general audience"
else:
    level = "Professional/Academic"
    action = "Simplify if possible"
```

## Advanced Analysis

### Custom Feature Engineering

Add domain-specific features:

```python
class CustomExtractor(FeatureExtractor):
    def extract_domain_features(self, text):
        # Medical domain example
        medical_terms = ["diagnosis", "treatment", "symptom", "prescription"]
        term_count = sum(1 for term in medical_terms if term in text.lower())
        
        return {
            "medical_term_density": term_count / len(text.split()),
            "has_disclaimer": "consult" in text.lower()
        }

extractor = CustomExtractor()
features = extractor.extract_domain_features(text)
```

### Statistical Aggregation

Analyze feature distributions:

```python
import statistics

readability_scores = [
    extractor.extract_complexity(output)["flesch_reading_ease"]
    for output in outputs
]

print(f"Mean: {statistics.mean(readability_scores)}")
print(f"Median: {statistics.median(readability_scores)}")
print(f"StdDev: {statistics.stdev(readability_scores)}")
```

## Best Practices

1. **Always check features** in evaluation manifests
2. **Establish baselines** for your domain
3. **Monitor trends** over time
4. **Correlate with quality** scores
5. **Use for filtering** expensive evaluations
6. **Document patterns** you discover

## Performance Notes

Feature extraction is fast (<10ms per text) and runs automatically during evaluation. It adds negligible overhead compared to LLM judge calls.

## Next Steps

- Understand [Core Concepts](core-concepts.md)
- Learn about [Evaluation Results](../api/core/manifest.md)
- See [Examples](examples.md) of feature analysis
