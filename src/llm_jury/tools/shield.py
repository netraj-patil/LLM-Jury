"""
Hallucination Shield.
A 'Firewall' tool that validates agentic steps (tool calls, reasoning) against a consensus of models
to prevent compounding hallucinations.
"""

from dataclasses import dataclass
from typing import Any, Optional, Dict, List

from llm_jury.core.evaluator import JuryEvaluator
from llm_jury.metrics.base import Metric
from llm_jury.metrics.predefined import GroundednessMetric

@dataclass
class ValidationResult:
    """
    The output of a shield validation check.
    
    Attributes:
        is_valid (bool): Whether the proposed action passed the jury's threshold.
        consensus_reasoning (str): Aggregated justification from the jury.
        confidence (float): The statistical confidence (0-1) of the verdict.
        metadata (Dict): Additional diagnostic info (latency, judge count).
    """
    is_valid: bool
    consensus_reasoning: str
    confidence: float
    metadata: Dict[str, Any]

class HallucinationShield:
    """
    Acts as a gatekeeper for agentic workflows.
    
    It allows an agent to submit a 'Proposed Step' (action/tool call) and verifies 
    its groundedness against the source context using the JuryEvaluator.
    """

    def __init__(self, jury_evaluator: JuryEvaluator):
        """
        Initialize the shield with an existing jury engine.
        
        Args:
            jury_evaluator (JuryEvaluator): The configured evaluation engine 
                                            (with judges and strategy already set).
        """
        self.jury = jury_evaluator

    def validate_step(
        self, 
        context_text: str, 
        proposed_action: str, 
        metric: Optional[Metric] = None
    ) -> ValidationResult:
        """
        Validates a proposed agent action against the provided context.

        Args:
            context_text (str): The 'Source Context' or 'State' the agent is working from.
            proposed_action (str): The tool call or text generation the agent wants to perform.
            metric (Metric): The criteria to judge by. Defaults to GroundednessMetric.

        Returns:
            ValidationResult: The verdict (Valid/Invalid) and reasoning.
        """
        # Default to Groundedness if no specific metric provided
        # "The jury must specifically evaluate the proposed step for Groundedness"
        check_metric = metric if metric else GroundednessMetric()

        # Execute the Jury Evaluation
        # We treat the 'proposed_action' as the 'output' to be judged.
        eval_result = self.jury.evaluate(
            context=context_text,
            output=proposed_action,
            metric=check_metric
        )

        # Aggregate Reasoning (Consensus Reasoning) 
        # We combine unique points from judges to form a summary.
        # In a real app, you might use an LLM to summarize these textually.
        # Here, we concatenate unique reasons to provide full transparency.
        reasons = [s.reasoning for s in eval_result.manifest.individual_scores if s.reasoning]
        # Simple deduplication while preserving order
        unique_reasons = list(dict.fromkeys(reasons))
        consensus_summary = " | ".join(unique_reasons)

        return ValidationResult(
            is_valid=eval_result.is_valid,
            consensus_reasoning=consensus_summary,
            confidence=eval_result.confidence,
            metadata=eval_result.manifest.metadata
        )

    def get_recovery_guidance(self, result: ValidationResult) -> str:
        """
        Provides feedback to the agent if a step is rejected.

        Args:
            result (ValidationResult): The result from validate_step.

        Returns:
            str: A formatted instruction prompt for the agent.
        """
        if result.is_valid:
            return "Step Verified. Proceed."

        # Construct failure feedback
        guidance = (
            "ACTION REJECTED by Hallucination Shield.\n"
            "Reasoning: The proposed action was found to be unsupported by the context.\n"
            f"Jury Feedback: {result.consensus_reasoning}\n"
            "Guidance: Please revise your action to ensure it relies ONLY on the provided source text."
        )
        return guidance