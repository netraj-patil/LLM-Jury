"""
Base Judge Interface.
Defines the abstract contract for all judge implementations (LLM-based, Heuristic, or Custom).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

# Forward reference for type checking to avoid circular imports
if TYPE_CHECKING:
    from llm_jury.core.manifest import JudgeScore

class Judge(ABC):
    """
    Abstract base class for all judges in the LLM Jury system.
    
    Attributes:
        name (str): The unique identifier or name for this judge (e.g., "gpt-4-turbo", "heuristic-1").
    """

    def __init__(self, name: str):
        """
        Initialize the judge with a name.

        Args:
            name (str): Identifier for the judge.
        """
        self.name = name

    @abstractmethod
    def evaluate_score(self, prompt: str, context: Any) -> JudgeScore:
        """
        Evaluates the provided prompt and context to produce a score.

        this method is responsible for:
        1. Invoking the judgment logic (LLM API call or local function).
        2. Parsing the output (e.g., extracting JSON or Regex matches).
        3. Returning a structured JudgeScore object containing the score, 
           reasoning, and optional metadata map.

        Args:
            prompt (str): The evaluation instruction or criteria (e.g., "Rate groundedness 1-5").
            context (Any): The content to evaluate. This can be a string (raw text) 
                           or a dictionary containing {source, output, retrieval_context}.

        Returns:
            JudgeScore: A structured object containing the numerical score, 
                        textual reasoning, and metadata.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"