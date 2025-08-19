"""Get the build number for the current PR."""

import json
import subprocess
import sys

import click


def get_latest_build_for_pr() -> str:
    """Get the build number for the current PR.

    Extracts the Buildkite build number from the current PR's checks.
    Handles error conditions like no PR, no checks, or no Buildkite checks.

    Returns:
        str: The build number

    Raises:
        SystemExit: If an error occurs (with error message printed to stderr)
    """
    try:
        # First check if we're on a branch with a PR
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "number"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            click.echo("Error: No PR found for current branch", err=True)
            sys.exit(1)

        # Get PR checks
        result = subprocess.run(
            ["gh", "pr", "checks", "--json", "name,state,link"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            click.echo("Error: Could not retrieve PR checks", err=True)
            sys.exit(1)

        if not result.stdout.strip():
            click.echo("Error: No checks found for current PR", err=True)
            sys.exit(1)

        try:
            checks = json.loads(result.stdout)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON response from gh pr checks", err=True)
            sys.exit(1)

        # Find Buildkite check
        buildkite_check = None
        for check in checks:
            if "buildkite" in check.get("name", "").lower():
                buildkite_check = check
                break

        if not buildkite_check:
            click.echo("Error: No Buildkite checks found for current PR", err=True)
            sys.exit(1)

        # Extract build number from link
        link = buildkite_check.get("link", "")
        if not link:
            click.echo("Error: Buildkite check has no link", err=True)
            sys.exit(1)

        # Extract build number (last part of URL after final slash)
        build_number = link.rstrip("/").split("/")[-1]

        if not build_number or not build_number.isdigit():
            click.echo(f"Error: Could not extract valid build number from link: {link}", err=True)
            sys.exit(1)

        return build_number

    except subprocess.SubprocessError as e:
        click.echo(f"Error: Failed to run gh command: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(1)


@click.command(name="bk-latest-build-for-pr")
def bk_latest_build_for_pr():
    """Get the build number for the current PR.

    Extracts the Buildkite build number from the current PR's checks.
    Handles error conditions like no PR, no checks, or no Buildkite checks.
    """
    build_number = get_latest_build_for_pr()
    click.echo(build_number)
