import os
from pathlib import Path
from typing import Any, Dict

import dagster as dg
import dspy
from dspy.teleprompt import MIPROv2
from pydantic import Field

from dspy_modules.connections_metrics import success_metric
from dspy_modules.puzzle import load_puzzles_from_csv, shuffle_and_split_puzzles
from dspy_modules.solver import ConnectionsSolver, create_dataset
from project_dspy.defs.resources import DSPyResource


def _get_main_model():
    """Get the configured main Gemini model for Connections predictions."""
    main_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    api_key = os.getenv("GEMINI_API_KEY", "")

    return dspy.LM(
        model=f"gemini/{main_model}", api_key=api_key, temperature=0.7, max_tokens=8192
    )


class DSPyModelBuilder(dg.Component, dg.Model, dg.Resolvable):
    """Reusable component for building and optimizing DSPy Connections solver models.

    This component creates baseline DSPy models, runs optimization with MIPROv2,
    and evaluates model performance for Connections puzzle solving.
    """

    model_name: str = Field(description="Name of the DSPy model to create")
    connections_data_path: str = Field(description="Path to Connections CSV data file")
    performance_threshold: float = Field(
        default=0.3, description="Minimum performance for optimization"
    )
    optimization_enabled: bool = Field(
        default=True, description="Whether to run optimization"
    )
    train_test_split: float = Field(
        default=0.25, description="Fraction of data to use for training"
    )
    eval_subset_size: int = Field(
        default=10, description="Number of puzzles to evaluate on for demo"
    )
    num_threads: int = Field(
        default=4, description="Number of threads for dspy.Evaluate"
    )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # start_puzzle_data_asset
        @dg.asset(
            name="connections_puzzle_data",
            compute_kind="python",
            group_name="data",
            description="Loads and splits Connections puzzle data for training and evaluation",
        )
        def puzzle_data_asset(
            context: dg.AssetExecutionContext,
        ) -> Dict[str, Any]:
            """Load and split Connections puzzle data."""

            # Get absolute path to connections data
            data_path = Path(self.connections_data_path)
            if not data_path.is_absolute():
                data_path = Path.cwd() / data_path

            context.log.info(f"Loading Connections data from: {data_path}")

            if not data_path.exists():
                raise FileNotFoundError(f"Connections data not found at: {data_path}")

            # Load puzzles
            puzzles = load_puzzles_from_csv(str(data_path))
            context.log.info(f"Loaded {len(puzzles)} puzzles")

            # Split data
            train_puzzles, test_puzzles = shuffle_and_split_puzzles(
                puzzles, self.train_test_split
            )

            # Take subset for evaluation if specified
            eval_puzzles = (
                test_puzzles[: self.eval_subset_size]
                if self.eval_subset_size
                else test_puzzles
            )

            context.log.info(
                f"Split: {len(train_puzzles)} training, {len(eval_puzzles)} evaluation puzzles"
            )

            context.add_output_metadata(
                {
                    "total_puzzles": len(puzzles),
                    "train_puzzles": len(train_puzzles),
                    "eval_puzzles": len(eval_puzzles),
                    "train_test_split": self.train_test_split,
                    "data_path": str(data_path),
                }
            )

            return {
                "train_puzzles": train_puzzles,
                "eval_puzzles": eval_puzzles,
                "total_puzzles": len(puzzles),
            }

        # end_puzzle_data_asset

        # start_baseline_model_asset
        @dg.asset(
            name=f"{self.model_name}_baseline_model",
            compute_kind="dspy",
            group_name="models",
            description=f"Baseline (unoptimized) {self.model_name} DSPy model",
            deps=["connections_puzzle_data"],
        )
        def baseline_model_asset(
            context: dg.AssetExecutionContext,
            dspy_resource: DSPyResource,
        ) -> Dict[str, Any]:
            """Create baseline DSPy Connections solver model."""
            # start_baseline_core
            # Configure DSPy
            dspy_resource.configure_dspy()

            # Create baseline model
            model = ConnectionsSolver()

            # Save baseline model
            model_path = dspy_resource.save_model(
                model, f"{self.model_name}_baseline", "latest"
            )
            # end_baseline_core

            context.log.info(f"Created baseline Connections solver: {self.model_name}")

            context.add_output_metadata(
                {
                    "model_name": f"{self.model_name}_baseline",
                    "model_path": str(model_path),
                    "model_type": "ConnectionsSolver",
                }
            )

            return {
                "model_name": f"{self.model_name}_baseline",
                "model_path": str(model_path),
                "version": "latest",
            }

        # end_baseline_model_asset

        # start_optimized_model_asset
        @dg.asset(
            name=f"{self.model_name}_baseline_performance",
            compute_kind="dspy",
            group_name="evaluation",
            description=f"Performance evaluation of baseline {self.model_name} model",
            deps=[
                f"{self.model_name}_baseline_model",
                "connections_puzzle_data",
            ],
        )
        def baseline_performance_asset(
            context: dg.AssetExecutionContext,
            dspy_resource: DSPyResource,
        ) -> Dict[str, Any]:
            """Evaluate baseline model performance on Connections puzzles."""

            # Configure DSPy
            dspy_resource.configure_dspy()

            # Load baseline model
            model = ConnectionsSolver()
            dspy_resource.load_model(model, f"{self.model_name}_baseline", "latest")

            # Load evaluation puzzles (simulate loading from previous asset)
            data_path = Path(self.connections_data_path)
            if not data_path.is_absolute():
                data_path = Path.cwd() / data_path

            puzzles = load_puzzles_from_csv(str(data_path))
            _, test_puzzles = shuffle_and_split_puzzles(puzzles, self.train_test_split)
            eval_puzzles = test_puzzles[: self.eval_subset_size]

            context.log.info(
                f"Evaluating baseline model on {len(eval_puzzles)} puzzles"
            )

            # Create dataset for dspy.Evaluate
            dataset = create_dataset(eval_puzzles)

            # Use dspy.Evaluate with threading for faster evaluation
            main_lm = _get_main_model()
            with dspy.context(lm=main_lm):
                evaluate = dspy.Evaluate(
                    devset=dataset,
                    metric=success_metric,
                    display_progress=True,
                    num_threads=self.num_threads,
                )

                result = evaluate(model)

            # Extract score from EvaluationResult
            score = result.score if hasattr(result, "score") else result
            success_rate = float(score) if score is not None else 0.0

            # Calculate additional metrics from predictions if available
            num_evaluated = len(eval_puzzles)

            performance = {
                "success_rate": success_rate,
                "num_evaluated": num_evaluated,
                "needs_optimization": success_rate < self.performance_threshold,
                "score": success_rate,  # For compatibility
            }

            context.log.info(
                f"Baseline Performance - Success Rate: {success_rate:.3f}, "
                f"Puzzles Evaluated: {num_evaluated}"
            )

            context.add_output_metadata(
                {
                    **performance,
                    "performance_threshold": self.performance_threshold,
                    "model_name": f"{self.model_name}_baseline",
                }
            )

            return performance

        # Only create optimization asset if enabled
        assets = [
            puzzle_data_asset,
            baseline_model_asset,
            baseline_performance_asset,
        ]

        if self.optimization_enabled:

            @dg.asset(
                name=f"{self.model_name}_optimized_model",
                compute_kind="dspy",
                group_name="models",
                description=f"MIPROv2 optimized {self.model_name} DSPy model",
                deps=[f"{self.model_name}_baseline_performance"],
            )
            def optimized_model_asset(
                context: dg.AssetExecutionContext,
                dspy_resource: DSPyResource,
            ) -> Dict[str, Any]:
                """Run DSPy optimization if performance is below threshold."""

                # Configure DSPy
                dspy_resource.configure_dspy()

                # Load baseline model
                baseline_model = ConnectionsSolver()
                dspy_resource.load_model(
                    baseline_model, f"{self.model_name}_baseline", "latest"
                )

                # Load puzzle data for optimization
                data_path = Path(self.connections_data_path)
                if not data_path.is_absolute():
                    data_path = Path.cwd() / data_path

                puzzles = load_puzzles_from_csv(str(data_path))
                train_puzzles, _ = shuffle_and_split_puzzles(
                    puzzles, self.train_test_split
                )

                # Take subset for optimization (smaller for speed)
                opt_puzzles = train_puzzles[: min(20, len(train_puzzles))]

                # Create datasets for optimization
                train_dataset = create_dataset(opt_puzzles)

                # Split into train/val (60/40 split)
                train_size = int(0.6 * len(train_dataset))
                trainset = train_dataset[:train_size]
                valset = train_dataset[train_size:]

                context.log.info(
                    f"Starting MIPROv2 optimization with {len(trainset)} train, {len(valset)} val examples"
                )

                # Define optimization metric - use the simple success metric
                def optimization_metric(example, pred, trace=None):
                    try:
                        # Use the simple success metric that matches your solver
                        return success_metric(example, pred, trace)
                    except Exception as e:
                        context.log.warning(f"Metric calculation failed: {e}")
                        return False

                # Get model parameters for Gemini
                main_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
                api_key = os.getenv("GEMINI_API_KEY", "")

                params = {
                    "api_key": api_key,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                }

                optimizer = MIPROv2(
                    auto="light",  # Use light mode for faster optimization
                    metric=optimization_metric,
                    teacher_settings=dict(lm=dspy.LM(f"gemini/{main_model}", **params)),
                    prompt_model=dspy.LM(f"gemini/{main_model}", **params),
                    num_threads=4,
                )

                optimized_model = optimizer.compile(
                    baseline_model,
                    trainset=trainset,
                    valset=valset,
                )

                # Save optimized model
                model_path = dspy_resource.save_model(
                    optimized_model, f"{self.model_name}_optimized", "latest"
                )

                context.log.info(f"Optimization complete. Model saved to: {model_path}")

                context.add_output_metadata(
                    {
                        "model_name": f"{self.model_name}_optimized",
                        "model_path": str(model_path),
                        "optimization_method": "MIPROv2",
                        "base_model": f"{self.model_name}_baseline",
                    }
                )

                return {
                    "model_name": f"{self.model_name}_optimized",
                    "model_path": str(model_path),
                    "version": "latest",
                    "optimized": True,
                }

            @dg.asset(
                name=f"{self.model_name}_optimized_performance",
                compute_kind="dspy",
                group_name="evaluation",
                description=f"Performance evaluation of optimized {self.model_name} model",
                deps=[
                    f"{self.model_name}_optimized_model",
                    "connections_puzzle_data",
                ],
            )
            def optimized_performance_asset(
                context: dg.AssetExecutionContext,
                dspy_resource: DSPyResource,
            ) -> Dict[str, Any]:
                """Evaluate optimized model performance."""

                # Configure DSPy
                dspy_resource.configure_dspy()

                # Load optimized model
                model = ConnectionsSolver()
                dspy_resource.load_model(
                    model, f"{self.model_name}_optimized", "latest"
                )

                # Load evaluation puzzles
                data_path = Path(self.connections_data_path)
                if not data_path.is_absolute():
                    data_path = Path.cwd() / data_path

                puzzles = load_puzzles_from_csv(str(data_path))
                _, test_puzzles = shuffle_and_split_puzzles(
                    puzzles, self.train_test_split
                )
                eval_puzzles = test_puzzles[: self.eval_subset_size]

                context.log.info(
                    f"Evaluating optimized model on {len(eval_puzzles)} puzzles"
                )

                # Create dataset for dspy.Evaluate
                dataset = create_dataset(eval_puzzles)

                # Use dspy.Evaluate with threading for faster evaluation
                main_lm = _get_main_model()
                with dspy.context(lm=main_lm):
                    evaluate = dspy.Evaluate(
                        devset=dataset,
                        metric=success_metric,
                        display_progress=True,
                        num_threads=self.num_threads,
                    )

                    result = evaluate(model)

                # Extract score from EvaluationResult
                score = result.score if hasattr(result, "score") else result
                success_rate = float(score) if score is not None else 0.0

                # Calculate additional metrics
                num_evaluated = len(eval_puzzles)

                performance = {
                    "success_rate": success_rate,
                    "num_evaluated": num_evaluated,
                    "model_type": "optimized",
                    "score": success_rate,  # For compatibility
                }

                context.log.info(
                    f"Optimized Performance - Success Rate: {success_rate:.3f}, "
                    f"Puzzles Evaluated: {num_evaluated}"
                )

                context.add_output_metadata(
                    {
                        **performance,
                        "performance_threshold": self.performance_threshold,
                        "model_name": f"{self.model_name}_optimized",
                    }
                )

                return performance

            # end_optimized_model_asset

            assets.extend([optimized_model_asset, optimized_performance_asset])

        # start_evaluation_asset
        # Evaluation happens within the performance assets above
        # end_evaluation_asset

        return dg.Definitions(assets=assets)
