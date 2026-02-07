# Hallucination Shield 🛡️

The Hallucination Shield is a specialized tool for agentic AI workflows that validates reasoning steps before execution, preventing error cascades.

## Overview

Agentic systems (agents that use tools and make decisions) can compound errors:

```
Step 1: Agent hallucinates a fact
  ↓
Step 2: Next reasoning builds on hallucination
  ↓
Step 3: Error cascade continues
  ↓
Result: Complete failure
```

The Shield acts as a checkpoint between steps:

```
Step 1: Proposed → Shield validates → ✓ Approved
  ↓
Step 2: Proposed → Shield validates → ✓ Approved
  ↓
Step 3: Proposed → Shield validates → ✗ Rejected
  ↓
Recovery: Agent revises step 3
```

## Basic Usage

```python
from llm_jury.tools.shield import HallucinationShield
from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.judges.llm_judge import LLMJudge
from langchain_openai import ChatOpenAI

# Setup jury
judges = [
    LLMJudge(ChatOpenAI(model="gpt-4o"), name="gpt-4"),
    LLMJudge(ChatOpenAI(model="gpt-3.5-turbo"), name="gpt-3.5"),
]
jury = JuryEvaluator(judges=judges)

# Create shield
shield = HallucinationShield(jury_evaluator=jury)

# Validate agent step
context = "User profile shows: Name: John, Age: 30, Location: NYC"
proposed_action = "Send email to John at his Paris office"

validation = shield.validate_step(
    context_text=context,
    proposed_action=proposed_action
)

if validation.is_valid:
    # Execute the action
    execute_tool_call(proposed_action)
else:
    # Get recovery guidance
    guidance = shield.get_recovery_guidance(validation)
    print(guidance)
    # Re-prompt agent with guidance
```

## How It Works

1. **Agent proposes action**: Based on current context/state
2. **Shield validates**: Uses jury to check groundedness
3. **Decision**:
   - Valid → Action proceeds
   - Invalid → Agent receives feedback
4. **Agent adjusts**: Uses feedback to revise action

## Integration with Agents

### LangChain Agent Integration

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool

def validated_tool_wrapper(tool_func, shield, context):
    """Wraps a tool with validation."""
    def wrapped_tool(action_input):
        # Validate before execution
        validation = shield.validate_step(
            context_text=context,
            proposed_action=action_input
        )
        
        if not validation.is_valid:
            return f"Action rejected: {validation.consensus_reasoning}"
        
        # Execute if valid
        return tool_func(action_input)
    
    return wrapped_tool

# Wrap tools
database_query_validated = validated_tool_wrapper(
    database_query_tool,
    shield,
    current_context
)

# Use in agent
tools = [
    Tool(
        name="database",
        func=database_query_validated,
        description="Query the database"
    )
]
```

### Custom Agent Loop

```python
class ShieldedAgent:
    def __init__(self, llm, shield, tools):
        self.llm = llm
        self.shield = shield
        self.tools = tools
        self.context = []
    
    def run(self, task):
        while not self.is_complete(task):
            # Agent proposes next action
            thought = self.llm.generate(self.context + [task])
            action = self.parse_action(thought)
            
            # Validate with shield
            validation = self.shield.validate_step(
                context_text=str(self.context),
                proposed_action=action
            )
            
            if validation.is_valid:
                # Execute
                result = self.execute_tool(action)
                self.context.append({"action": action, "result": result})
            else:
                # Provide feedback
                guidance = self.shield.get_recovery_guidance(validation)
                self.context.append({"feedback": guidance})
                # Agent will retry on next iteration
```

## Validation Result

The `validate_step` method returns a `ValidationResult`:

```python
@dataclass
class ValidationResult:
    is_valid: bool                  # Pass/fail
    consensus_reasoning: str        # Why it passed/failed
    confidence: float               # Jury agreement (0-1)
    metadata: Dict[str, Any]        # Additional details
```

### Interpreting Results

```python
validation = shield.validate_step(...)

print(f"Valid: {validation.is_valid}")
print(f"Confidence: {validation.confidence:.2%}")
print(f"Reasoning: {validation.consensus_reasoning}")

# Check metadata
judges_count = len(validation.metadata.get("individual_scores", []))
print(f"Judges consulted: {judges_count}")
```

## Custom Metrics

By default, the shield uses `GroundednessMetric`. You can specify custom criteria:

```python
from llm_jury.metrics.base import Metric

class SafetyMetric(Metric):
    def __init__(self):
        super().__init__(
            name="Safety",
            description="Ensures action is safe to execute",
            scale_min=1.0,
            scale_max=5.0
        )
    
    def get_prompt(self, context=None):
        return """
        Evaluate if this action is safe to execute.
        
        CRITERIA:
        5: Completely safe, no risks
        3: Some minor risks but acceptable
        1: Dangerous, should not execute
        """

safety_metric = SafetyMetric()

validation = shield.validate_step(
    context_text=context,
    proposed_action=action,
    metric=safety_metric
)
```

## Recovery Guidance

When validation fails, get actionable feedback:

```python
validation = shield.validate_step(...)

if not validation.is_valid:
    guidance = shield.get_recovery_guidance(validation)
    print(guidance)
    
    # Send guidance back to agent
    agent.provide_feedback(guidance)
```

Example guidance output:

```
ACTION REJECTED by Hallucination Shield.
Reasoning: The proposed action was found to be unsupported by the context.
Jury Feedback: The action references a "Paris office" but the context only 
mentions "Location: NYC". No Paris office is documented.
Guidance: Please revise your action to ensure it relies ONLY on the provided 
source text.
```

## Use Cases

### RAG Agent with Tool Calls

```python
# Agent retrieves documents
retrieved_docs = rag_system.retrieve(query)

# Agent proposes answer
proposed_answer = agent.generate(retrieved_docs)

# Validate before returning to user
validation = shield.validate_step(
    context_text=retrieved_docs,
    proposed_action=proposed_answer
)

if validation.is_valid:
    return proposed_answer
else:
    # Re-prompt agent
    return agent.regenerate(validation.consensus_reasoning)
```

### Multi-Step Planning

```python
plan = agent.create_plan(task)

for step in plan:
    # Validate each step
    validation = shield.validate_step(
        context_text=current_state,
        proposed_action=step
    )
    
    if validation.is_valid:
        execute(step)
        current_state = update_state(step)
    else:
        # Replan from this point
        plan = agent.replan(current_state, validation.consensus_reasoning)
```

### Database Query Validation

```python
def safe_database_query(query, schema):
    # Check if query is grounded in schema
    validation = shield.validate_step(
        context_text=f"Database schema: {schema}",
        proposed_action=f"Execute query: {query}"
    )
    
    if validation.confidence < 0.7:
        return "Query validation uncertain, manual review required"
    
    if validation.is_valid:
        return execute_query(query)
    else:
        return f"Invalid query: {validation.consensus_reasoning}"
```

## Configuration

### Jury Configuration

Configure the underlying jury for different sensitivities:

```python
# Strict validation (high threshold)
strict_jury = JuryEvaluator(
    judges=[judge1, judge2, judge3, judge4, judge5],
    strategy=ConsensusStrategy(threshold=0.8)
)
strict_shield = HallucinationShield(strict_jury)

# Permissive validation (lower threshold)
permissive_jury = JuryEvaluator(
    judges=[judge1, judge2],
    strategy=MajorityVoting()
)
permissive_shield = HallucinationShield(permissive_jury)
```

### Threshold-Based Actions

```python
validation = shield.validate_step(...)

if validation.confidence < 0.5:
    # Very uncertain - require human review
    route_to_human(validation)
elif validation.is_valid:
    # Confident and valid - proceed
    execute(action)
else:
    # Confident but invalid - block and provide feedback
    block_with_guidance(validation)
```

## Performance Considerations

### Latency

Shield validation adds latency (jury evaluation time):
- 3 judges × 500ms = ~500ms total (parallel)
- Consider this when designing agent loops

### Cost

Each validation costs API calls:
- 3 judges = 3 API calls per step
- For cost optimization: use fewer judges or cheaper models

### Caching

Cache validations for repeated actions:

```python
from functools import lru_cache

class CachedShield(HallucinationShield):
    @lru_cache(maxsize=1000)
    def validate_step(self, context_text, proposed_action, metric=None):
        return super().validate_step(context_text, proposed_action, metric)
```

## Best Practices

1. **Use 3-5 judges** for balance of accuracy and speed
2. **Set appropriate thresholds** based on risk tolerance
3. **Provide clear feedback** to agents for recovery
4. **Log all validations** for debugging
5. **Monitor false positives/negatives** and adjust
6. **Cache when possible** to reduce costs

## Advanced Patterns

### Multi-Level Validation

```python
# Quick check first
fast_validation = fast_shield.validate_step(context, action)

if fast_validation.is_valid and fast_validation.confidence > 0.8:
    # High confidence, proceed
    execute(action)
elif not fast_validation.is_valid and fast_validation.confidence > 0.8:
    # High confidence rejection, block
    reject(action)
else:
    # Uncertain, use thorough validation
    thorough_validation = thorough_shield.validate_step(context, action)
    if thorough_validation.is_valid:
        execute(action)
```

### Adaptive Thresholds

```python
def get_threshold(task_criticality):
    if task_criticality == "high":
        return 0.9  # Very strict
    elif task_criticality == "medium":
        return 0.7
    else:
        return 0.5  # Permissive

validation = shield.validate_step(...)
threshold = get_threshold(current_task.criticality)

if validation.confidence >= threshold:
    # Meets threshold for this task
    execute(action)
```

## Next Steps

- Understand [Core Concepts](core-concepts.md)
- Learn about [Judges](judges.md) and [Metrics](metrics.md)
- See [Examples](examples.md) of agent integration
