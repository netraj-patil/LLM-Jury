"""
LLM Judge Implementation.
Wraps LangChain models to act as judges in the LLM Jury system.
"""

import re
import json
from typing import Any, Dict, Optional, Union

# LangChain Imports for broad model support
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from llm_jury.judges.base import Judge
# Assuming JudgeScore is defined in core.manifest as per the roadmap
from llm_jury.core.manifest import JudgeScore 

class LLMJudge(Judge):
    """
    A concrete Judge implementation that uses a LangChain model to evaluate text.
    Supports any model compatible with BaseChatModel or BaseLanguageModel.
    """

    def __init__(
        self, 
        model: Union[BaseChatModel, BaseLanguageModel], 
        name: Optional[str] = None
    ):
        """
        Initialize the LLM Judge.

        Args:
            model: An instance of a LangChain ChatModel (e.g., ChatOpenAI, ChatAnthropic)
                   or LLM.
            name: Optional specific name. If None, defaults to the model's class/name.
        """
        # Infer a name if not provided (e.g., "ChatOpenAI" or "gpt-4")
        judge_name = name or getattr(model, "name", model.__class__.__name__)
        super().__init__(name=judge_name)
        
        self.model = model

    def evaluate_score(self, prompt: str, context: Any) -> JudgeScore:
        """
        Executes the evaluation using the LangChain model and parses the result.
        
        Args:
            prompt (str): The specific metric prompt (e.g., "Rate Groundedness 1-5...").
            context (Any): The input data (text, dict of source/output, etc.).
            
        Returns:
            JudgeScore: Structured score with reasoning and metadata.
        """
        # Prepare the Input Context
        # formatting the context into a string representation for the LLM
        formatted_context = self._format_context(context)
        
        # Construct Messages
        # We wrap the evaluation instructions in a system-like manner or combined prompt
        final_prompt = (
            f"{prompt}\n\n"
            f"--- CONTEXT TO EVALUATE ---\n"
            f"{formatted_context}\n\n"
            f"--- OUTPUT FORMAT ---\n"
            f"Return your response in the following format:\n"
            f"Score: <float>\n"
            f"Reasoning: <text explanation>\n"
            f"Metrics: <JSON dictionary of sub-metrics if applicable>"
        )

        # Invoke LangChain Model
        try:
            if isinstance(self.model, BaseChatModel):
                messages = [
                    SystemMessage(content="You are an impartial AI Judge. Evaluate the context based on the criteria provided."),
                    HumanMessage(content=final_prompt)
                ]
                response = self.model.invoke(messages)
                raw_output = response.content
            else:
                # Fallback for standard LLMs (non-chat)
                raw_output = self.model.invoke(final_prompt)
        except Exception as e:
            # Return a default 'failure' score if the API call fails
            return self._create_error_score(str(e))

        # Parse the Output (Structured Parsing)
        return self._parse_output(raw_output)

    def _format_context(self, context: Any) -> str:
        """Helper to convert complex context dicts into a readable string."""
        if isinstance(context, str):
            return context
        if isinstance(context, dict):
            # Format as "Key: Value"
            return "\n".join([f"{k.upper()}:\n{v}" for k, v in context.items()])
        return str(context)

    def _parse_output(self, raw_text: str) -> JudgeScore:
        """
        Parses the raw LLM output using Regex/JSON extraction as per requirements.
        Expected format includes 'Score:', 'Reasoning:', and optional 'Metrics:'.
        """
        score_obj = JudgeScore()
        score_obj.judge_id = self.name
        
        # Extract Score (looking for "Score: 3.5" or similar)
        score_match = re.search(r"Score:\s*([-+]?\d*\.\d+|\d+)", raw_text, re.IGNORECASE)
        if score_match:
            try:
                score_obj.score = float(score_match.group(1))
            except ValueError:
                score_obj.score = 0.0
        
        # Extract Reasoning
        # Captures everything after "Reasoning:" until the end or next section
        reasoning_match = re.search(r"Reasoning:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            # validation to stop if we hit "Metrics:"
            reasoning_text = reasoning_match.group(1).strip()
            if "Metrics:" in reasoning_text:
                reasoning_text = reasoning_text.split("Metrics:")[0].strip()
            score_obj.reasoning = reasoning_text
        else:
            score_obj.reasoning = raw_text # Fallback: treat whole text as reasoning

        # Extract Metadata/Sub-metrics (JSON or Key-Value)
        # Attempt to find JSON block first
        json_match = re.search(r"Metrics:\s*(\{.*?\})", raw_text, re.DOTALL)
        if json_match:
            try:
                score_obj.metrics_metadata = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        return score_obj

    def _create_error_score(self, error_msg: str) -> JudgeScore:
        """Creates a valid JudgeScore object indicating a system failure."""
        error_score = JudgeScore()
        error_score.score = 0.0
        error_score.judge_id = self.name
        error_score.reasoning = f"SYSTEM ERROR: Failed to generate evaluation. {error_msg}"
        return error_score