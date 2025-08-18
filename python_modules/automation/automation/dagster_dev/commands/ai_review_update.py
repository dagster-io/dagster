"""Update PR title, body, and commit message with auto-prepare functionality."""

import json
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import Optional

import click
import dagster._check as check
from dagster._record import record


@record
class CommandResult:
    success: bool
    result: Optional[CompletedProcess]
    error_message: Optional[str]


def run_command_optional(cmd: list[str], description: str) -> CommandResult:
    """Run a command and return structured result - never exits."""
    click.echo(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return CommandResult(success=True, result=result, error_message=None)
    except subprocess.CalledProcessError as e:
        error_msg = f"Error {description}: {e}"
        click.echo(error_msg, err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        return CommandResult(success=False, result=None, error_message=error_msg)


def run_command_critical(cmd: list[str], description: str) -> CompletedProcess:
    """Run a command that must succeed - exits program on failure."""
    result = run_command_optional(cmd, description)
    if not result.success:
        sys.exit(1)
    return check.not_none(result.result)


def get_pr_number() -> str:
    """Get the current PR number from gh pr view."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            click.echo("❌ No PR found for current branch", err=True)
            click.echo("Please create a PR first using 'gt submit' or 'gh pr create'", err=True)
            sys.exit(1)
        pr_number = result.stdout.strip()
        click.echo(f"✅ Found PR #{pr_number}")
        return pr_number
    except Exception as e:
        click.echo(f"❌ Error checking PR: {e}", err=True)
        sys.exit(1)


def idempotent_gt_squash(base_branch: str = "master") -> CommandResult:
    """Idempotent gt squash that only squashes when needed and never fails."""
    # Check commit count first
    commit_count_result = run_command_optional(
        ["git", "log", "--oneline", f"{base_branch}..HEAD"], "counting commits"
    )

    if not commit_count_result.success:
        return CommandResult(success=False, result=None, error_message="Failed to count commits")

    result = check.not_none(commit_count_result.result)
    commit_count = len([line for line in result.stdout.strip().split("\n") if line.strip()])

    if commit_count <= 1:
        click.echo("✅ Branch already has single commit, no squashing needed")
        return CommandResult(success=True, result=None, error_message=None)

    # Multiple commits - attempt to squash
    click.echo(f"📦 Found {commit_count} commits, attempting to squash...")
    squash_result = run_command_optional(["gt", "squash", "--no-interactive"], "squashing commits")

    if squash_result.success:
        click.echo("✅ Commits squashed successfully")
        return squash_result

    # Squash failed - check if we're actually in desired state anyway
    final_count_result = run_command_optional(
        ["git", "log", "--oneline", f"{base_branch}..HEAD"],
        "recounting commits after failed squash",
    )

    if final_count_result.success:
        final_result = check.not_none(final_count_result.result)
        final_count = len(
            [line for line in final_result.stdout.strip().split("\n") if line.strip()]
        )
        if final_count <= 1:
            click.echo("✅ Branch ended up with single commit despite squash failure")
            return CommandResult(success=True, result=None, error_message=None)

    # Squash truly failed but don't break the automation
    click.echo("⚠️ Squash failed but continuing with multiple commits")
    return CommandResult(success=True, result=None, error_message="Squash failed but continuing")


def run_auto_prepare(context: Optional[dict] = None) -> None:
    """Run gt squash and gt submit if needed."""
    click.echo("🔧 Running auto-prepare operations...")

    # Determine the base branch to compare against
    base_branch = "master"  # default
    if context and context.get("previous_branch"):
        base_branch = context["previous_branch"]
        click.echo(f"Using previous branch in stack: {base_branch}")
    else:
        click.echo("Using default base branch: master")

    # Use idempotent squash wrapper
    click.echo("\n📦 Running idempotent squash...")
    idempotent_gt_squash(base_branch)

    # Try to submit
    click.echo("\n📤 Attempting to submit branch...")
    result = run_command_optional(["gt", "submit", "--no-interactive"], "submitting branch")
    if result.success:
        click.echo("✅ Branch submitted successfully")
    else:
        # Check if submit failed because already up to date
        if result.result and "All PRs up to date" in (result.result.stdout or ""):
            click.echo("i All PRs already up to date")
        else:
            click.echo("❌ Failed to submit branch - continuing anyway", err=True)


@click.command(name="ai-review-update")
@click.option("--title", required=True, help="PR title to set")
@click.option("--body", required=True, help="PR body/description to set")
@click.option("--commit-title", help="Optional custom commit title (defaults to PR title)")
@click.option(
    "--auto-prepare",
    is_flag=True,
    help="Automatically run gt squash and gt submit before updating PR",
)
@click.option(
    "--from-context",
    type=click.Path(exists=True, path_type=Path),
    help="Path to JSON context file from ai-review-analyze command",
)
def update_pr(
    title: str,
    body: str,
    commit_title: Optional[str],
    auto_prepare: bool,
    from_context: Optional[Path],
):
    """Update PR title, body, and commit message in one atomic operation.

    This command ensures synchronization between your GitHub PR and local git repository
    by updating both the remote PR metadata and the local commit message simultaneously.
    This prevents the common problem where PR descriptions and commit messages diverge
    over time, making it harder to understand the change history.

    SYNCHRONIZATION BEHAVIOR:
    - GitHub PR title ← matches → Local commit title (first line)
    - GitHub PR body ← matches → Local commit body (remaining lines)
    - Both are updated atomically to maintain consistency

    The command safely updates:
    1. GitHub PR title and body (via GitHub CLI)
    2. Local git commit message using `git commit --amend`
       - Commit title = PR title (or custom --commit-title)
       - Commit body = PR body (full description)

    WHY THIS MATTERS:
    - Keeps your development history clean and consistent
    - Makes it easy to understand changes when reviewing git log
    - Ensures PR descriptions accurately reflect the actual commit
    - Prevents confusion between what's described in GitHub vs git history

    All operations are executed serially to prevent git index locking issues.

    Examples:
        dagster-dev ai-review-update --title "Fix bug" --body "This fixes the issue with..."
        dagster-dev ai-review-update --title "New feature" --body "Adds support for..." --commit-title "feat: New feature"
        dagster-dev ai-review-update --auto-prepare --title "Fix" --body "..."
    """
    click.echo("🔄 Updating PR and commit message...")

    # Load context if provided
    context = None
    if from_context:
        with open(from_context) as f:
            context = json.load(f)

    # Step 0: Auto-prepare if requested
    if auto_prepare:
        run_auto_prepare(context)

    # Step 1: Verify PR exists (skip if we have context)
    if context and context.get("validation", {}).get("pr_exists"):
        pr_number = context["pr_number"]
        click.echo(f"\n1️⃣ Using PR #{pr_number} from context")
    else:
        click.echo("\n1️⃣ Verifying PR exists...")
        pr_number = get_pr_number()

    # Step 2: Update PR title
    click.echo("\n2️⃣ Updating PR title...")
    run_command_critical(["gh", "pr", "edit", "--title", title], "updating PR title")
    click.echo(f"✅ PR title updated: {title}")

    # Step 3: Update PR body
    click.echo("\n3️⃣ Updating PR body...")
    run_command_critical(["gh", "pr", "edit", "--body", body], "updating PR body")
    click.echo("✅ PR body updated")

    # Step 4: Update commit message
    click.echo("\n4️⃣ Updating commit message...")
    final_commit_title = commit_title if commit_title else title
    commit_message = f"{final_commit_title}\n\n{body}"

    run_command_critical(
        ["git", "commit", "--amend", "-m", commit_message], "updating commit message"
    )
    click.echo(f"✅ Commit message updated: {final_commit_title}")

    # Step 5: Display success and Graphite URL
    click.echo(f"\n🎉 Successfully updated PR #{pr_number}!")
    click.echo(
        f"🔗 Graphite PR View: https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}/"
    )
