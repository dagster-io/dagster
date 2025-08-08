import hashlib
import json
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from dagster_shared.record import record
from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from rich.console import Console
from rich.table import Table


@record
class Metric:
    """A metric to evaluate."""

    name: str
    criteria: str
    evaluation_steps: Optional[list[str]] = None

    def get_hash(self) -> str:
        """Generate a hash for this metric configuration."""
        content = self.criteria
        if self.evaluation_steps:
            content += "".join(self.evaluation_steps)
        return hashlib.sha256(content.encode()).hexdigest()[:8]

    @cached_property
    def geval(self) -> GEval:
        return GEval(
            name=self.name,
            criteria=self.criteria,
            evaluation_steps=self.evaluation_steps,
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
        )

    @property
    def flat_name(self) -> str:
        return self.name.lower().replace(" ", "_")

    @property
    def id(self) -> str:
        return f"{self.flat_name}-{self.get_hash()}"


@record
class EvalConfig:
    """Configuration for evaluation."""

    metrics: list[Metric]


def load_config(eval_dir: Path) -> EvalConfig:
    """Load and validate the evaluation configuration."""
    config_path = eval_dir / "eval.yaml"
    if not config_path.exists():
        raise click.UsageError(f"Configuration file {config_path} not found")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    return EvalConfig(metrics=[Metric(**metric) for metric in config_data["metrics"]])


def load_sessions(eval_dir: Path) -> dict[str, dict[str, Any]]:
    """Load all session files from the directory."""
    sessions = {}
    session_files = list(eval_dir.glob("*.json"))

    # Exclude cache files
    session_files = [f for f in session_files if not f.name.startswith("metric-")]

    for session_file in session_files:
        session_id = session_file.stem
        with open(session_file) as f:
            session_data = json.load(f)

        # Validate required fields
        if not isinstance(session_data, dict):
            raise click.UsageError(
                f"Warning: Skipping {session_file.name} - not a valid JSON object"
            )

        if (
            "input" not in session_data
            or "output" not in session_data
            or "timestamp" not in session_data
        ):
            raise click.UsageError(
                f"Warning: Skipping {session_file.name} - missing required fields"
            )

        sessions[session_id] = session_data

    if not sessions:
        raise click.UsageError("No valid session files found")

    return sessions


def load_results(eval_dir: Path, metric: Metric) -> dict[str, dict[str, Any]]:
    """Load cached results for a metric."""
    cache_file = eval_dir / f"metric-{metric.get_hash()}.json"

    if not cache_file.exists():
        return {}

    with open(cache_file) as f:
        return json.load(f)


def save_results(eval_dir: Path, metric: Metric, cache: dict[str, dict[str, Any]]) -> None:
    """Save cached results for a metric."""
    cache_file = eval_dir / f"metric-{metric.get_hash()}.json"

    # Write to temp file first for atomic update
    temp_file = cache_file.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(cache, f, indent=2)

    # Atomic rename
    temp_file.replace(cache_file)


def evaluate_sessions(
    sessions: dict[str, dict[str, Any]], metric: Metric, cached_results: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Evaluate sessions that aren't in cache."""
    # Find uncached sessions
    uncached_sessions = [
        (sid, sdata) for sid, sdata in sessions.items() if sid not in cached_results
    ]

    if not uncached_sessions:
        return cached_results

    # Create test cases
    test_cases = [
        LLMTestCase(
            input=str(session_data["input"]),
            actual_output=str(session_data["output"]),
        )
        for _, session_data in uncached_sessions
    ]

    # Run evaluation
    click.echo(f"Evaluating {len(test_cases)} sessions for metric '{metric.id}'...")
    results = evaluate(test_cases=test_cases, metrics=[metric.geval])

    # Update cache with new results
    new_cache = dict(cached_results)
    for (session_id, _), result in zip(uncached_sessions, results.test_results):
        assert result.metrics_data
        metric_result = result.metrics_data[0]  # We only have one metric per evaluation
        new_cache[session_id] = {
            "score": metric_result.score,
            "reason": metric_result.reason,
            "evaluated_at": datetime.now().isoformat(),
        }

    return new_cache


def display_results(
    sessions: dict[str, dict[str, Any]],
    all_results: dict[str, dict[str, dict[str, Any]]],
    metrics: list[Metric],
    show_fields: tuple[str, ...],
) -> None:
    """Display evaluation results in a table."""
    console = Console()

    # Display metrics summary
    console.print("\n[bold blue]Metrics Summary:[/bold blue]")
    for i, metric in enumerate(metrics, 1):
        console.print(
            f"  {i}. [yellow]{metric.name.capitalize()}[/yellow] ([dim]{metric.get_hash()}[/dim]): {metric.criteria}"
        )

    # Sort sessions by timestamp
    sorted_sessions = sorted(sessions.items(), key=lambda x: x[1]["timestamp"])

    # Create Rich table
    console.print()  # Add spacing before results
    table = Table(
        title="[bold cyan]📊 EVALUATION RESULTS[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
    )

    # Add columns
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Time", style="green", no_wrap=True)

    # Add custom fields as columns
    for field in show_fields:
        table.add_column(field.capitalize(), style="blue")

    for metric in metrics:
        table.add_column(metric.name.capitalize(), style="yellow", justify="center")

    # Add rows
    for session_id, session_data in sorted_sessions:
        # Parse timestamp for terse display
        timestamp = datetime.fromisoformat(session_data["timestamp"])
        time_str = timestamp.strftime("%m/%d %H:%M")

        row_data = [session_id[:8], time_str]

        # Add custom field values
        for field in show_fields:
            value = session_data.get(field, "")
            # Truncate long values and convert to string
            value_str = str(value) if value else "-"
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            row_data.append(value_str)

        for metric in metrics:
            if metric.id in all_results and session_id in all_results[metric.id]:
                score = all_results[metric.id][session_id]["score"]
                # Color code scores: green for high, yellow for medium, red for low
                score_str = f"{score:.2f}"
                if score >= 0.8:
                    score_str = f"[bold green]{score_str}[/bold green]"
                elif score >= 0.6:
                    score_str = f"[bold yellow]{score_str}[/bold yellow]"
                else:
                    score_str = f"[bold red]{score_str}[/bold red]"
                row_data.append(score_str)
            else:
                row_data.append("[dim]-[/dim]")

        table.add_row(*row_data)

    console.print(table)
    console.print()  # Add spacing after results


@click.command()
@click.argument("directory")
@click.option(
    "--show",
    "-s",
    multiple=True,
    help="Additional fields from session JSON to display as columns (can be specified multiple times)",
)
def main(directory: str, show: tuple[str, ...]) -> None:
    """Utility for performing evaluations over ai tool sessions.

    Expects a directory containing:
    * Session files: <uuid>.json files with the following schema:
      {
        "input": str,        # Required: The input prompt/question
        "output": str,       # Required: The AI's response
        "timestamp": str,    # Required: ISO format timestamp
        ...                  # Optional: Any additional fields (can be displayed with --show)
      }

    * Configuration file: eval.yaml with the following schema:
      metrics:
        - name: str                    # Display name for the metric
          criteria: str                # Evaluation criteria description
          evaluation_steps:            # Optional: Specific evaluation steps
            - str
            - str
            ...

    Example eval.yaml:
      metrics:
        - name: "Accuracy"
          criteria: "How accurate is the response to the question?"
          evaluation_steps:
            - "Check if the response directly answers the question"
            - "Verify factual correctness"
        - name: "Completeness"
          criteria: "Does the response fully address all aspects of the question?"
    """
    eval_dir = Path(directory)

    if not eval_dir.exists():
        raise click.UsageError(f"Directory {directory} does not exist")

    # Load configuration
    config = load_config(eval_dir)

    # Load sessions
    sessions = load_sessions(eval_dir)

    # Process each metric
    all_results = {}
    for metric in config.metrics:
        # Load cache
        cached_results = load_results(eval_dir, metric)

        # Evaluate uncached sessions
        updated_results = evaluate_sessions(sessions, metric, cached_results)

        # Save updated cache
        if updated_results != cached_results:
            save_results(eval_dir, metric, updated_results)

        # Store results for display
        all_results[metric.id] = updated_results

    # Display results
    display_results(sessions, all_results, config.metrics, show)


if __name__ == "__main__":
    main()
