"""Update PR title, body, and commit message."""

import subprocess
import sys
from typing import Optional

import click


def run_command(cmd: list[str], description: str) -> subprocess.CompletedProcess:
    """Run a command and handle errors gracefully."""
    click.echo(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        click.echo(f"Error {description}: {e}", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        sys.exit(1)


def get_pr_number() -> str:
    """Get the current PR number from gh pr view."""
    result = run_command(
        ["gh", "pr", "view", "--json", "number", "--jq", ".number"], "getting PR number"
    )
    return result.stdout.strip()


@click.command(name="update-pr-and-commit")
@click.option("--title", required=True, help="PR title to set")
@click.option("--body", required=True, help="PR body/description to set")
@click.option("--commit-title", help="Optional custom commit title (defaults to PR title)")
def update_pr(title: str, body: str, commit_title: Optional[str]):
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
        dagster-dev update-pr-and-commit --title "Fix bug" --body "This fixes the issue with..."
        dagster-dev update-pr-and-commit --title "New feature" --body "Adds support for..." --commit-title "feat: New feature"
    """
    click.echo("🔄 Updating PR and commit message...")

    # Step 1: Verify PR exists
    click.echo("\n1️⃣ Verifying PR exists...")
    try:
        pr_number = get_pr_number()
        click.echo(f"✅ Found PR #{pr_number}")
    except Exception:
        click.echo("❌ No PR found for current branch", err=True)
        click.echo("Please create a PR first using 'gt submit' or 'gh pr create'", err=True)
        sys.exit(1)

    # Step 2: Update PR title
    click.echo("\n2️⃣ Updating PR title...")
    run_command(["gh", "pr", "edit", "--title", title], "updating PR title")
    click.echo(f"✅ PR title updated: {title}")

    # Step 3: Update PR body
    click.echo("\n3️⃣ Updating PR body...")
    run_command(["gh", "pr", "edit", "--body", body], "updating PR body")
    click.echo("✅ PR body updated")

    # Step 4: Update commit message
    click.echo("\n4️⃣ Updating commit message...")
    final_commit_title = commit_title if commit_title else title
    commit_message = f"{final_commit_title}\n\n{body}"

    run_command(["git", "commit", "--amend", "-m", commit_message], "updating commit message")
    click.echo(f"✅ Commit message updated: {final_commit_title}")

    # Step 5: Display success and Graphite URL
    click.echo(f"\n🎉 Successfully updated PR #{pr_number}!")
    click.echo(
        f"🔗 Graphite PR View: https://app.graphite.dev/github/pr/dagster-io/dagster/{pr_number}/"
    )
