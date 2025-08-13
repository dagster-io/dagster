"""Business logic for run commands - pure functions for easy testing."""

import json
from typing import Any

import click


def process_run_view_response(graphql_response: dict[str, Any]) -> dict[str, Any]:
    """Process GraphQL response for run view command.

    Args:
        graphql_response: Raw GraphQL response dict

    Returns:
        Processed API response dict

    Raises:
        click.ClickException: If response contains errors
    """
    run_result = graphql_response.get("runOrError")

    if not run_result:
        raise click.ClickException("No run data returned from API")

    # Handle error cases
    if run_result.get("__typename") == "RunNotFoundError":
        error_msg = f"Run not found: {run_result.get('message', 'Unknown error')}"
        raise click.ClickException(error_msg)

    if run_result.get("__typename") == "PythonError":
        error_msg = f"API Error: {run_result.get('message', 'Unknown error')}"
        raise click.ClickException(error_msg)

    # Transform to REST-like format
    run_data = run_result
    tags_dict = {tag["key"]: tag["value"] for tag in run_data.get("tags", [])}

    # Get stats data if available
    stats_data = run_data.get("stats", {})
    stats_summary = {}
    if stats_data and stats_data.get("__typename") == "RunStatsSnapshot":
        stats_summary = {
            "steps_succeeded": stats_data.get("stepsSucceeded", 0),
            "steps_failed": stats_data.get("stepsFailed", 0),
            "materializations": stats_data.get("materializations", 0),
            "expectations": stats_data.get("expectations", 0),
            "enqueued_time": stats_data.get("enqueuedTime"),
            "launch_time": stats_data.get("launchTime"),
            "start_time": stats_data.get("startTime"),
            "end_time": stats_data.get("endTime"),
        }

    return {
        "id": run_data["id"],
        "run_id": run_data["runId"],
        "status": run_data["status"],
        "pipeline_name": run_data.get("pipelineName"),
        "job_name": run_data.get("jobName"),
        "creation_time": run_data.get("creationTime"),
        "start_time": run_data.get("startTime"),
        "end_time": run_data.get("endTime"),
        "can_terminate": run_data.get("canTerminate"),
        "root_run_id": run_data.get("rootRunId"),
        "parent_run_id": run_data.get("parentRunId"),
        "tags": tags_dict,
        "assets": [asset["key"]["path"] for asset in run_data.get("assets", [])],
        "stats": stats_summary,
    }


def format_run_view_output(api_response: dict[str, Any], as_json: bool) -> str:
    """Format API response for output.

    Args:
        api_response: Processed API response dict
        as_json: Whether to format as JSON

    Returns:
        Formatted output string
    """
    if as_json:
        return json.dumps(api_response, indent=2)
    else:
        # Human-readable format
        output_lines = []
        for key, value in api_response.items():
            if isinstance(value, list):
                output_lines.append(f"{key}: {len(value)} items")
            elif isinstance(value, dict):
                output_lines.append(f"{key}: {json.dumps(value)}")
            else:
                output_lines.append(f"{key}: {value}")
        return "\n".join(output_lines)
