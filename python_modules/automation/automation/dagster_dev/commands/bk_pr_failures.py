"""Get PR failures from current PR to Buildkite build to failed jobs to annotations."""

import json
import os
from typing import Any, Optional

import click
import requests

from automation.dagster_dev.commands.bk_build_status import get_build_jobs
from automation.dagster_dev.commands.bk_latest_build_for_pr import get_latest_build_for_pr


def get_failed_jobs(org: str, pipeline: str, build_number: str) -> list[dict[str, Any]]:
    """Get only failed jobs for a build."""
    all_jobs = get_build_jobs(org, pipeline, build_number)
    return [job for job in all_jobs if job.get("state", "").lower() == "failed"]


def get_build_annotations(org: str, pipeline: str, build_number: str) -> dict[str, Any]:
    """Get annotations for a build using Buildkite API."""
    import os

    # Get API token
    token = os.environ.get("BUILDKITE_API_TOKEN")
    if not token:
        click.echo("Warning: BUILDKITE_API_TOKEN not set, skipping annotations", err=True)
        return {"annotations": [], "total_count": 0}

    # Call Buildkite API for annotations
    url = f"https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}/annotations"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers, params={"per_page": 20})
        response.raise_for_status()
        annotations = response.json()

        return {
            "annotations": annotations if isinstance(annotations, list) else [],
            "total_count": len(annotations) if isinstance(annotations, list) else 0,
        }

    except requests.exceptions.RequestException as e:
        click.echo(f"Warning: Could not fetch annotations: {e}", err=True)
        return {"annotations": [], "total_count": 0}
    except json.JSONDecodeError as e:
        click.echo(f"Warning: Invalid JSON in annotations response: {e}", err=True)
        return {"annotations": [], "total_count": 0}


def get_job_logs(org: str, pipeline: str, build_number: str, job_id: str) -> Optional[str]:
    """Get job logs from Buildkite API."""
    import os

    # Get API token
    token = os.environ.get("BUILDKITE_API_TOKEN")
    if not token:
        click.echo(
            f"Warning: BUILDKITE_API_TOKEN not set, skipping logs for job {job_id}", err=True
        )
        return None

    # Call Buildkite API for job logs
    url = f"https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}/jobs/{job_id}/log"
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/plain"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    except requests.exceptions.RequestException as e:
        click.echo(f"Warning: Could not fetch logs for job {job_id}: {e}", err=True)
        return None


def format_job_name(job: dict[str, Any]) -> str:
    """Extract and format job name."""
    return job.get("name", "Unknown Job")


def create_temp_log_dir(build_number: str) -> str:
    """Create temporary directory for log files."""
    import os
    import tempfile

    base_dir = os.environ.get("DAGSTER_GIT_REPO_DIR", tempfile.gettempdir())
    log_dir = os.path.join(base_dir, ".tmp", "bk-logs", build_number)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def download_failed_job_logs(
    org: str, pipeline: str, build_number: str, failed_jobs: list[dict[str, Any]]
) -> dict[str, str]:
    """Download logs for failed jobs and return job_id -> log_file_path mapping."""
    import os
    import re

    log_dir = create_temp_log_dir(build_number)
    job_log_paths = {}

    for job in failed_jobs:
        job_id = job.get("id")
        job_name = format_job_name(job)

        if not job_id:
            continue

        # Get logs
        logs = get_job_logs(org, pipeline, build_number, job_id)
        if not logs:
            continue

        # Create safe filename
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", job_name)
        log_filename = f"{safe_name}.log"
        log_path = os.path.join(log_dir, log_filename)

        # Save logs to file
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(logs)
            job_log_paths[job_id] = log_path
        except Exception as e:
            click.echo(f"Warning: Could not save logs for job {job_name}: {e}", err=True)

    return job_log_paths


def create_failure_summary(
    org: str,
    pipeline: str,
    build_number: str,
    failed_jobs: list[dict[str, Any]],
    annotations: dict[str, Any],
    job_log_paths: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Create a comprehensive failure summary."""
    error_annotations = [
        ann
        for ann in annotations.get("annotations", [])
        if ann.get("style") in ["error", "warning"]
    ]

    return {
        "build": {
            "org": org,
            "pipeline": pipeline,
            "number": build_number,
            "url": f"https://buildkite.com/{org}/{pipeline}/builds/{build_number}",
        },
        "summary": {
            "failed_jobs": len(failed_jobs),
            "annotations": len(error_annotations),
            "status": "failed" if failed_jobs else "passed",
            "logs_downloaded": job_log_paths is not None and len(job_log_paths) > 0,
            "logs_directory": f"{os.environ.get('DAGSTER_GIT_REPO_DIR', '/tmp')}/.tmp/bk-logs/{build_number}"
            if job_log_paths
            else None,
            "total_log_files": len(job_log_paths) if job_log_paths else 0,
        },
        "failed_jobs": [
            {
                "id": (job_id := job.get("id")),
                "name": format_job_name(job),
                "state": job.get("state"),
                "web_url": job.get("web_url"),
                "log_url": job.get("log_url"),
                "log_file_path": job_log_paths.get(job_id) if job_log_paths and job_id else None,
                "exit_status": job.get("exit_status"),
                "finished_at": job.get("finished_at"),
                "started_at": job.get("started_at"),
                "job_type": job.get("type"),
                "parallel_group_index": job.get("parallel_group_index"),
                "parallel_group_total": job.get("parallel_group_total"),
            }
            for job in failed_jobs
        ],
        "annotations": [
            {
                "context": ann.get("context", "unknown"),
                "style": ann.get("style", "info"),
                "body_html": ann.get("body_html", ""),
                "created_at": ann.get("created_at"),
            }
            for ann in error_annotations
        ],
    }


def print_failure_summary(
    org: str,
    pipeline: str,
    build_number: str,
    failed_jobs: list[dict[str, Any]],
    annotations: dict[str, Any],
    job_log_paths: Optional[dict[str, str]] = None,
) -> None:
    """Print a formatted failure summary."""
    build_url = f"https://buildkite.com/{org}/{pipeline}/builds/{build_number}"

    click.echo(f"\n🔍 PR Failure Analysis for {org}/{pipeline} #{build_number}")
    click.echo(f"🔗 {build_url}")
    click.echo("=" * 60)

    # Failed jobs section
    if failed_jobs:
        click.echo(f"\n❌ **Failed Jobs ({len(failed_jobs)} total)**:")
        for job in failed_jobs:
            job_name = format_job_name(job)
            job_id = job.get("id")

            click.echo(f"  - {job_name}")

            # Show log file path if available
            if job_log_paths and job_id and job_id in job_log_paths:
                log_path = job_log_paths[job_id]
                click.echo(f"    📄 Log: {log_path}")
    else:
        click.echo("\n✅ **No failed jobs found**")
        return

    # Annotations section
    error_annotations = [
        ann
        for ann in annotations.get("annotations", [])
        if ann.get("style") in ["error", "warning"]
    ]

    if error_annotations:
        click.echo(f"\n🚨 **Build Annotations ({len(error_annotations)} errors/warnings)**:")
        for ann in error_annotations:
            context = ann.get("context", "unknown")
            style = ann.get("style", "info")
            emoji = "❌" if style == "error" else "⚠️"
            click.echo(f"  {emoji} {context}")

            # Extract meaningful content from HTML
            body = ann.get("body_html", "")
            if body and len(body) < 500:  # Only show short content
                # Simple HTML stripping for basic content
                import re

                text_content = re.sub(r"<[^>]+>", "", body).strip()
                if text_content:
                    lines = text_content.split("\n")[:3]  # First 3 lines only
                    for line in lines:
                        if line.strip():
                            click.echo(f"    {line.strip()}")
    else:
        click.echo("\n📝 **No error annotations found**")
        click.echo("    (Raw logs may contain error details)")

    # Action summary
    click.echo(
        f"\n📊 **Summary**: {len(failed_jobs)} failed jobs, {len(error_annotations)} annotations"
    )
    click.echo("🔧 **Next Steps**: Review failed jobs and annotations above for specific fixes")


@click.command(name="bk-pr-failures")
@click.argument("build_number", required=False)
@click.option("--org", default="dagster", help="Organization slug (default: dagster)")
@click.option(
    "--pipeline", default="dagster-dagster", help="Pipeline slug (default: dagster-dagster)"
)
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.option("--logs", is_flag=True, help="Download logs for failed jobs")
def bk_pr_failures(
    build_number: Optional[str], org: str, pipeline: str, output_json: bool, logs: bool
):
    """Get PR failures: current PR → Buildkite build → failed jobs → annotations.

    Complete workflow from current PR to detailed failure analysis in a single command.
    Shows failed jobs and structured error annotations for quick diagnosis.

    If no BUILD_NUMBER is provided, automatically detects the build number
    from the current PR's Buildkite checks.

    Examples:
        dagster-dev bk-pr-failures           # Current PR failures
        dagster-dev bk-pr-failures 133650    # Specific build failures
        dagster-dev bk-pr-failures --json    # JSON output for current PR
        dagster-dev bk-pr-failures 133650 --org myorg --pipeline mypipeline
    """
    # Get build number if not provided
    if not build_number:
        if not output_json:
            click.echo("No build number provided, detecting from current PR...")
        build_number = get_latest_build_for_pr()

    if not output_json:
        click.echo(f"Analyzing failures for {org}/{pipeline} #{build_number}...")

    # Get failed jobs
    failed_jobs = get_failed_jobs(org, pipeline, build_number)

    # Get annotations
    annotations = get_build_annotations(org, pipeline, build_number)

    # Download logs if requested
    job_log_paths = None
    if logs and failed_jobs:
        if not output_json:
            click.echo("Downloading logs for failed jobs...")
        job_log_paths = download_failed_job_logs(org, pipeline, build_number, failed_jobs)

    # Output results
    if output_json:
        summary = create_failure_summary(
            org, pipeline, build_number, failed_jobs, annotations, job_log_paths
        )
        click.echo(json.dumps(summary, indent=2))
    else:
        print_failure_summary(org, pipeline, build_number, failed_jobs, annotations, job_log_paths)
