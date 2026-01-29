"""
Predefined Metrics.
Standard implementations for common LLM evaluation tasks like Groundedness and Hallucination.
"""

from typing import Any, Dict
from llm_jury.metrics.base import Metric

class GroundednessMetric(Metric):
    """
    Evaluates whether the model's output is fully supported by the provided source context.
    Critical for RAG (Retrieval-Augmented Generation) applications to prevent 'hallucinations' 
    where the model invents facts not present in the retrieved documents.
    """

    def __init__(self):
        super().__init__(
            name="Groundedness", 
            description="Measures if the answer is derived solely from the source context.",
            scale_min=1.0,
            scale_max=5.0
        )

    def get_prompt(self, context: Any = None) -> str:
        """
        Generates a prompt asking the judge to verify facts against the source.
        
        Expected context structure (Dict):
        - source_text: The retrieved context or reference document.
        - output_text: The model's generated answer.
        """
        # Safe extraction of strings if context is a dict
        source = context.get("source_text", "") if isinstance(context, dict) else ""
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        
        return (
            "You are a Groundedness Judge. Your task is to determine if the 'Model Output' "
            "contains any information that is NOT supported by the 'Source Text'.\n\n"
            "--- SOURCE TEXT ---\n"
            f"{source}\n\n"
            "--- MODEL OUTPUT ---\n"
            f"{output}\n\n"
            "--- SCORING CRITERIA ---\n"
            "5: The output is fully supported by the source text. Every claim has a clear basis.\n"
            "4: The output is mostly supported, with minor rephrasing that keeps the meaning.\n"
            "3: The output is partially supported but includes minor details not found in the source.\n"
            "2: The output contains significant information not present in the source.\n"
            "1: The output is largely unrelated to the source or contradicts it.\n\n"
            "Provide your verdict as a score between 1 and 5."
        )


class HallucinationMetric(Metric):
    """
    Evaluates the presence of fabricated information, logical inconsistencies, or 
    non-factual statements within the output, independent of a specific source text.
    Useful for general chat or creative writing where 'grounding' is less strict but 
    internal consistency and factual accuracy (world knowledge) are required.
    """

    def __init__(self):
        super().__init__(
            name="Hallucination", 
            description="Measures the presence of fabricated or logically inconsistent information.",
            scale_min=0.0,
            scale_max=1.0  # 0 = No Hallucination (Good), 1 = Hallucination (Bad)
        )

    def get_prompt(self, context: Any = None) -> str:
        """
        Generates a prompt asking the judge to identify logical flaws or fabrications.
        
        Expected context structure (Dict):
        - output_text: The model's generated answer to check.
        - input_prompt: The original user question (optional but helpful).
        """
        output = context.get("output_text", "") if isinstance(context, dict) else ""
        user_input = context.get("input_prompt", "") if isinstance(context, dict) else ""
        
        return (
            "You are a Hallucination Judge. Evaluate the 'Model Output' for logical consistency, "
            "factual correctness (general world knowledge), and relevance to the 'User Input'.\n\n"
            "--- USER INPUT ---\n"
            f"{user_input}\n\n"
            "--- MODEL OUTPUT ---\n"
            f"{output}\n\n"
            "--- SCORING CRITERIA ---\n"
            "0.0: No hallucination. The text is logically sound and factually accurate.\n"
            "0.5: Minor inconsistencies or ambiguous statements.\n"
            "1.0: Definite hallucination. The text contains fabrications, contradictions, or nonsense.\n\n"
            "Provide your verdict as a score between 0.0 and 1.0."
        )