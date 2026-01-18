"""Get build status from Buildkite."""

import json
import os
import sys
from typing import Any, Optional

import click
import requests

from automation.dagster_dev.commands.bk_latest_build_for_pr import get_latest_build_for_pr


def get_buildkite_token() -> str:
    """Get Buildkite API token from environment."""
    token = os.environ.get("BUILDKITE_API_TOKEN")
    if not token:
        click.echo("Error: BUILDKITE_API_TOKEN environment variable not set", err=True)
        click.echo("Please set your Buildkite API token:", err=True)
        click.echo("export BUILDKITE_API_TOKEN='your_token_here'", err=True)
        sys.exit(1)
    return token


def get_build_jobs(org: str, pipeline: str, build_number: str) -> list[dict[str, Any]]:
    """Get all jobs for a build from Buildkite API."""
    token = get_buildkite_token()

    url = f"https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        build_data = response.json()
        jobs = build_data.get("jobs", [])
        return jobs if isinstance(jobs, list) else []

    except requests.exceptions.RequestException as e:
        click.echo(f"Error calling Buildkite API: {e}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON response: {e}", err=True)
        sys.exit(1)


def get_build_status(org: str, pipeline: str, build_number: str) -> dict[str, list[dict[str, Any]]]:
    """Get all job statuses for a build and filter by state."""
    results = {"running": [], "passed": [], "failed": []}

    # Get all jobs from the build
    all_jobs = get_build_jobs(org, pipeline, build_number)

    # Filter jobs by state
    for job in all_jobs:
        state = job.get("state", "").lower()
        if state in results:
            results[state].append(job)

    return results


def format_job_name(job: dict[str, Any]) -> str:
    """Extract and format job name."""
    return job.get("name", "Unknown Job")


def create_json_summary(
    org: str, pipeline: str, build_number: str, results: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """Create a JSON-serializable summary of build status."""
    passed_jobs = results["passed"]
    running_jobs = results["running"]
    failed_jobs = results["failed"]
    total_active = len(passed_jobs) + len(running_jobs) + len(failed_jobs)

    # Determine overall status
    if failed_jobs:
        status = "failed"
        status_message = "There are failed jobs that need attention"
    elif running_jobs:
        status = "running"
        status_message = "Build in progress"
    else:
        status = "passed"
        status_message = "Build completed successfully"

    return {
        "build": {"org": org, "pipeline": pipeline, "number": build_number},
        "summary": {
            "passed": len(passed_jobs),
            "running": len(running_jobs),
            "failed": len(failed_jobs),
            "total_active": total_active,
        },
        "status": status,
        "status_message": status_message,
        "jobs": {
            "passed": [
                {"id": job.get("id"), "name": format_job_name(job), "state": job.get("state")}
                for job in passed_jobs
            ],
            "running": [
                {"id": job.get("id"), "name": format_job_name(job), "state": job.get("state")}
                for job in running_jobs
            ],
            "failed": [
                {"id": job.get("id"), "name": format_job_name(job), "state": job.get("state")}
                for job in failed_jobs
            ],
        },
    }


def print_status_summary(
    org: str, pipeline: str, build_number: str, results: dict[str, list[dict[str, Any]]]
) -> None:
    """Print a formatted summary of build status."""
    click.echo(f"\n🔍 Build Status Summary for {org}/{pipeline} #{build_number}")
    click.echo("=" * 60)

    # Passed jobs
    passed_jobs = results["passed"]
    click.echo(f"\n🟢 **Passed Jobs ({len(passed_jobs)} total)**:")
    if passed_jobs:
        for job in passed_jobs:
            click.echo(f"  - {format_job_name(job)}")
    else:
        click.echo("  (none)")

    # Running jobs
    running_jobs = results["running"]
    click.echo(f"\n🔄 **Running Jobs ({len(running_jobs)} total)**:")
    if running_jobs:
        for job in running_jobs:
            click.echo(f"  - {format_job_name(job)}")
    else:
        click.echo("  (none)")

    # Failed jobs
    failed_jobs = results["failed"]
    click.echo(f"\n❌ **Failed Jobs ({len(failed_jobs)} total)**:")
    if failed_jobs:
        for job in failed_jobs:
            click.echo(f"  - {format_job_name(job)}")
    else:
        click.echo("  (none)")

    # Summary
    total_active = len(passed_jobs) + len(running_jobs) + len(failed_jobs)
    click.echo(
        f"\n📊 **Summary**: {len(passed_jobs)} passed, {len(running_jobs)} running, {len(failed_jobs)} failed ({total_active} total active jobs)"
    )

    if failed_jobs:
        click.echo("⚠️  **Action Required**: There are failed jobs that need attention!")
    elif running_jobs:
        click.echo("⏳ **Status**: Build in progress...")
    else:
        click.echo("✅ **Status**: Build completed successfully!")


@click.command(name="bk-build-status")
@click.argument("build_number", required=False)
@click.option("--org", default="dagster", help="Organization slug (default: dagster)")
@click.option(
    "--pipeline", default="dagster-dagster", help="Pipeline slug (default: dagster-dagster)"
)
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def bk_build_status(build_number: Optional[str], org: str, pipeline: str, output_json: bool):
    """Get build status from Buildkite.

    Shows a summary of running, passed, and failed jobs for a specific build.
    Filters out broken/skipped jobs to focus on active build status.

    If no BUILD_NUMBER is provided, automatically detects the build number
    from the current PR's Buildkite checks.

    Examples:
        dagster-dev bk-build-status           # Use current PR's build
        dagster-dev bk-build-status 131813    # Specific build number
        dagster-dev bk-build-status --json    # JSON output for current PR
        dagster-dev bk-build-status 131813 --org myorg --pipeline mypipeline
    """
    # If no build number provided, get it from the current PR
    if not build_number:
        if not output_json:
            click.echo("No build number provided, detecting from current PR...")
        build_number = get_latest_build_for_pr()

    if not output_json:
        click.echo(f"Fetching build status for {org}/{pipeline} #{build_number}...")

    # Get build status
    results = get_build_status(org, pipeline, build_number)

    # Output results
    if output_json:
        summary = create_json_summary(org, pipeline, build_number, results)
        click.echo(json.dumps(summary, indent=2))
    else:
        print_status_summary(org, pipeline, build_number, results)
