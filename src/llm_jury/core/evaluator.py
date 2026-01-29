"""
Core Evaluation Engine.
Orchestrates the interaction between Judges, Metrics, and Aggregation Strategies
to produce final Evaluation Results.
"""

import concurrent.futures
from typing import List, Dict, Any, Union, Optional
from datetime import datetime

# Component Imports
from llm_jury.judges.base import Judge
from llm_jury.metrics.base import Metric
from llm_jury.strategies.base import AggregationStrategy
from llm_jury.strategies.consensus import MajorityVoting
from llm_jury.features.extractor import FeatureExtractor
from llm_jury.core.manifest import (
    EvaluationResult, 
    BatchEvaluationResult, 
    JuryManifest, 
    JudgeScore
)

class JuryEvaluator:
    """
    The central engine that coordinates the evaluation process.
    
    It manages the pool of judges, applies the chosen metric prompts, extracts 
    text features, and aggregates the results into a final verdict.
    """

    def __init__(
        self, 
        judges: List[Judge], 
        strategy: Optional[AggregationStrategy] = None
    ):
        """
        Initialize the Jury Evaluator.

        Args:
            judges (List[Judge]): A list of Judge instances (e.g., LLMJudge) to form the panel.
            strategy (AggregationStrategy): The method to resolve disagreements. 
                                            Defaults to MajorityVoting.
        """
        self.judges = judges
        # Default to Majority Voting if no strategy provided
        self.strategy = strategy if strategy else MajorityVoting()
        self.feature_extractor = FeatureExtractor()

    def add_judge(self, judge: Judge) -> None:
        """Adds a new judge to the existing panel."""
        self.judges.append(judge)

    def set_strategy(self, strategy: AggregationStrategy) -> None:
        """Updates the aggregation strategy (e.g., switching from Consensus to WeightedSum)."""
        self.strategy = strategy

    def evaluate(
        self, 
        context: Any, 
        output: str, 
        metric: Metric
    ) -> EvaluationResult:
        """
        Evaluates a single output against a specific metric.

        Process:
        1. Feature Extraction: Analyzes the output text for complexity/stats.
        2. Prompt Generation: Creates the specific instruction using the Metric.
        3. Judgment: Queries all judges in parallel.
        4. Normalization: Standardizes scores to [0, 1].
        5. Aggregation: Combines scores using the active Strategy.
        6. Manifest Creation: Packages everything into an audit trail.

        Args:
            context (Any): The source material (retrieved docs) or input prompt.
            output (str): The model generation to be evaluated.
            metric (Metric): The definition of criteria (e.g., Groundedness).

        Returns:
            EvaluationResult: The final scored object with full manifest.
        """
        # 1. Feature Extraction
        # We extract features from the 'output' as it's the primary text being judged.
        text_features = self.feature_extractor.extract_text_metrics(output)
        complexity_features = self.feature_extractor.extract_complexity(output)
        special_features = self.feature_extractor.extract_special_words(output)
        
        # Merge all features into one dict
        all_features = {**text_features, **complexity_features, **special_features}

        # 2. Prepare Context for Judges
        # If context is not a dict, wrap it. If it is, ensure output is present.
        eval_context = context if isinstance(context, dict) else {"source": context}
        if isinstance(eval_context, dict):
            eval_context["output_text"] = output

        # Generate the prompt from the metric
        prompt = metric.get_prompt(eval_context)

        # 3. Parallel Execution of Judges
        # Using ThreadPoolExecutor to minimize latency for API-based judges
        judge_scores: List[JudgeScore] = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.judges)) as executor:
            # Create a map of future -> judge to track who is who
            future_to_judge = {
                executor.submit(judge.evaluate_score, prompt, eval_context): judge 
                for judge in self.judges
            }
            
            for future in concurrent.futures.as_completed(future_to_judge):
                judge_ref = future_to_judge[future]
                try:
                    score_obj = future.result()
                    # Ensure judge_id is set correctly if the judge didn't set it
                    if score_obj.judge_id == "unknown":
                        score_obj.judge_id = judge_ref.name
                    
                    # 4. Scale Validation & Conditional Normalization
                    # Check if the chosen strategy requires normalized inputs (floats 0.0-1.0)
                    # or if it prefers raw discrete votes (integers 1-5).
                    
                    # We assume Weighted strategies need [0,1] to work correctly.
                    # MajorityVoting prefers raw numbers to count "votes".
                    # Note: We use string checks to avoid circular imports of specific Strategy classes.
                    strategy_name = self.strategy.__class__.__name__
                    should_normalize = strategy_name in ["WeightedSum", "WeightedAverage", "ConsensusStrategy"]
                    
                    if should_normalize:
                        # Normalize the score in place using the metric's defined scale
                        score_obj.score = metric.normalize(score_obj.score)
                    
                    judge_scores.append(score_obj)
                except Exception as e:
                    # Log failure but don't crash the whole jury
                    # In a real system, you might add a 'FailedJudgeScore' here
                    print(f"Judge {judge_ref.name} failed: {e}")

        # 5. Aggregation
        if not judge_scores:
             return EvaluationResult(
                 final_score=0.0, 
                 is_valid=False, 
                 confidence=0.0, 
                 manifest=JuryManifest(timestamp=datetime.now())
             )

        agg_result = self.strategy.aggregate(judge_scores)

        # 6. Build Manifest and Result
        manifest = JuryManifest(
            individual_scores=judge_scores,
            features=all_features,
            metadata={
                "metric_name": metric.name,
                "strategy_used": self.strategy.__class__.__name__,
                "aggregation_metadata": agg_result.metadata
            },
            timestamp=datetime.now()
        )

        # Determine validity (Example logic: Score > 0.5 normalized or > 3 raw)
        # We normalize the final aggregated score to determine validity in a standard way
        normalized_final_score = metric.normalize(agg_result.score)
        is_valid = normalized_final_score >= 0.5  # Default threshold

        return EvaluationResult(
            final_score=agg_result.score,
            is_valid=is_valid,
            confidence=agg_result.confidence,
            manifest=manifest
        )

    def evaluate_batch(
        self, 
        inputs: Dict[str, Dict[str, Any]], 
        metrics: List[Metric]
    ) -> BatchEvaluationResult:
        """
        Runs evaluations for multiple inputs or multiple metrics.
        
        Args:
            inputs (Dict): Map of ID -> Context Dict (must include 'output' and 'source').
            metrics (List[Metric]): List of metrics to apply to every input.
            
        Returns:
            BatchEvaluationResult: Container with all results mapped by ID.
        """
        batch_results = {}

        # Simple sequential loop for batching inputs (can be parallelized further)
        for item_id, context_data in inputs.items():
            output_text = context_data.get("output", "")
            # If context_data is the context itself
            
            for metric in metrics:
                # Create a unique key for the result: "ItemID_MetricName"
                result_key = f"{item_id}_{metric.name}"
                
                result = self.evaluate(
                    context=context_data,
                    output=output_text,
                    metric=metric
                )
                batch_results[result_key] = result

        return BatchEvaluationResult(results=batch_results)