"""Analyze PR context and repository state in machine-friendly format."""

import json
import subprocess
import sys
from typing import Any

import click

from automation.dagster_dev.commands.diff_summarizer import (
    format_summary_for_ai,
    get_smart_diff_summary,
)


def run_command(cmd: list[str], description: str) -> subprocess.CompletedProcess:
    """Run a command and handle errors gracefully."""
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


def get_stack_info(
    stack_only: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Get stack information using the gt-stack command."""
    # Get current branch info
    current_result = run_command(
        ["dagster-dev", "gt-stack", "--current-only"], "getting current branch info"
    )
    current_branches = json.loads(current_result.stdout)
    current_branch_info = current_branches[0] if current_branches else None

    # Get full stack structure
    stack_cmd = ["dagster-dev", "gt-stack"]
    if stack_only:
        stack_cmd.append("--stack")

    stack_result = run_command(stack_cmd, "getting stack structure")
    all_branches = json.loads(stack_result.stdout)

    return all_branches, current_branch_info


def find_previous_branch(
    all_branches: list[dict[str, Any]], current_branch_name: str
) -> str | None:
    """Find the previous branch in the stack (the one after the current branch)."""
    current_index = None

    # Find the current branch index
    for i, branch in enumerate(all_branches):
        if branch["name"] == current_branch_name and branch["is_current"]:
            current_index = i
            break

    if current_index is None:
        return None

    # The previous branch is the next one in the list (stacks are shown in reverse order)
    if current_index + 1 < len(all_branches):
        return all_branches[current_index + 1]["name"]

    return None


def get_changes_info(
    current_branch: str, previous_branch: str | None, use_smart_summary: bool = False
) -> dict[str, Any]:
    """Get changes information for the current branch."""
    if not previous_branch:
        # If no previous branch, compare against master
        diff_range = f"master..{current_branch}"
    else:
        diff_range = f"{previous_branch}..{current_branch}"

    # Get diff stats
    diff_result = run_command(
        ["git", "diff", "--stat", diff_range], f"getting diff stats for {diff_range}"
    )

    # Get detailed diff for summary (or smart summary)
    diff_detail = None
    if use_smart_summary:
        try:
            smart_summary = get_smart_diff_summary(diff_range)
            smart_formatted = format_summary_for_ai(smart_summary)
        except Exception:
            # Fallback to regular analysis if smart summary fails
            diff_detail = run_command(
                ["git", "diff", diff_range], f"getting detailed diff for {diff_range}"
            )
            smart_summary = None
            smart_formatted = None
    else:
        diff_detail = run_command(
            ["git", "diff", diff_range], f"getting detailed diff for {diff_range}"
        )
        smart_summary = None
        smart_formatted = None

    # Get commit messages
    log_result = run_command(
        ["git", "log", "--oneline", diff_range], f"getting commit log for {diff_range}"
    )

    # Parse diff stats
    stat_lines = [line.strip() for line in diff_result.stdout.strip().split("\n") if line.strip()]
    files_changed = 0
    additions = 0
    deletions = 0
    modified_files = []

    for line in stat_lines:
        if " file" in line and " changed" in line:
            # Summary line: "3 files changed, 100 insertions(+), 27 deletions(-)"
            parts = line.split(",")
            files_part = parts[0].strip()
            if files_part:
                files_changed = int(files_part.split()[0])

            for part in parts[1:]:
                stripped_part = part.strip()
                if "insertion" in stripped_part:
                    additions = int(stripped_part.split()[0])
                elif "deletion" in stripped_part:
                    deletions = int(stripped_part.split()[0])
        elif "|" in line and ("+" in line or "-" in line):
            # File line: "path/to/file.py | 10 +++++++---"
            filename = line.split("|")[0].strip()
            if filename:
                modified_files.append(filename)

    # Parse commits
    commits = []
    for line in log_result.stdout.strip().split("\n"):
        if line.strip():
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                commits.append({"hash": parts[0], "message": parts[1]})

    # Generate diff summary
    diff_summary = "No changes"
    if modified_files:
        if len(modified_files) == 1:
            diff_summary = f"Modified {modified_files[0]}"
        elif len(modified_files) <= 3:
            diff_summary = f"Modified {', '.join(modified_files)}"
        else:
            diff_summary = (
                f"Modified {len(modified_files)} files: {', '.join(modified_files[:2])}, ..."
            )

        # Add a hint about the nature of changes
        if use_smart_summary and smart_summary:
            # Use smart summary categorization
            category = smart_summary.change_category.value
            if category == "tests":
                diff_summary += " (test changes)"
            elif category == "documentation":
                diff_summary += " (documentation changes)"
            elif category == "new_feature":
                diff_summary += " (new feature)"
            elif category == "bug_fix":
                diff_summary += " (bug fix)"
            elif "refactor" in category:
                diff_summary += " (refactoring)"
        else:
            # Fallback to content analysis
            if diff_detail is not None:
                diff_content = diff_detail.stdout.lower()
                if "test" in diff_content and (
                    "def test_" in diff_content or "pytest" in diff_content
                ):
                    diff_summary += " (includes tests)"
                elif r"\.md" in str(modified_files):
                    diff_summary += " (documentation changes)"

    result = {
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "diff_summary": diff_summary,
        "modified_files": modified_files,
        "commits": commits,
        "diff_range": diff_range,
    }

    # Add smart summary data if available
    if use_smart_summary and smart_formatted:
        result["smart_analysis"] = smart_formatted

    return result


def check_pr_exists() -> str | None:
    """Check if a PR exists for the current branch."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Expected when no PR exists for the branch
        if e.returncode == 1:
            return None
        # Unexpected error - re-raise
        raise


def get_git_status() -> str:
    """Get git status."""
    result = run_command(["git", "status", "--porcelain"], "getting git status")
    return "clean" if not result.stdout.strip() else "dirty"


def needs_squash() -> bool:
    """Check if branch needs squashing (has multiple commits)."""
    try:
        result = subprocess.run(
            ["gt", "log", "--stack"], capture_output=True, text=True, check=True
        )
        # Count commits (rough heuristic)
        commit_lines = [
            line
            for line in result.stdout.split("\n")
            if line.strip()
            and len(line.strip()) >= 10
            and all(c in "0123456789abcdef" for c in line.strip()[:10])
        ]
        return len(commit_lines) > 1
    except subprocess.CalledProcessError as e:
        click.echo(f"Warning: Could not check if squash needed: {e}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        return False


def needs_submit() -> bool:
    """Check if branch needs submitting."""
    try:
        result = subprocess.run(
            ["gt", "log", "--stack"], capture_output=True, text=True, check=True
        )
        return "need submit" in result.stdout.lower() or "local changes" in result.stdout.lower()
    except subprocess.CalledProcessError as e:
        click.echo(f"Warning: Could not check if submit needed: {e}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        return False


@click.command(name="ai-review-analyze")
@click.option(
    "--human/--json",
    "output_human",
    default=False,
    help="Output in human-readable format (JSON is default)",
)
@click.option(
    "--minimal",
    is_flag=True,
    default=False,
    help="Minimize output by excluding full stack structure (keeps only current branch info)",
)
@click.option(
    "--smart-summary",
    is_flag=True,
    default=False,
    help="Use intelligent diff summarization instead of full diff content analysis",
)
def ai_review_analyze(output_human: bool, minimal: bool, smart_summary: bool) -> None:
    """Analyze PR context and repository state for AI consumption.

    This command consolidates all repository state checking into a single
    operation, providing comprehensive context about the current branch,
    stack structure, changes, and PR status.
    """
    try:
        # Get git branch
        current_branch_result = run_command(
            ["git", "branch", "--show-current"], "getting current branch"
        )
        current_branch = current_branch_result.stdout.strip()

        # Get stack information
        all_branches, current_branch_info = get_stack_info(stack_only=minimal)

        # Find previous branch
        previous_branch = find_previous_branch(all_branches, current_branch)

        # Get changes information
        changes_info = get_changes_info(current_branch, previous_branch, smart_summary)

        # Check PR status
        pr_number = check_pr_exists()

        # Get git status
        repo_state = get_git_status()

        # Check if operations are needed
        needs_squash_op = needs_squash()
        needs_submit_op = needs_submit()

        # Build result
        stack_info: dict[str, Any] = {"current_branch_info": current_branch_info}
        if not minimal:
            stack_info["stack_structure"] = all_branches

        result = {
            "current_branch": current_branch,
            "previous_branch": previous_branch,
            "pr_number": pr_number,
            "repository_state": repo_state,
            "stack_info": stack_info,
            "changes": changes_info,
            "validation": {
                "pr_exists": pr_number is not None,
                "branch_tracked": current_branch_info is not None,
                "working_directory_clean": repo_state == "clean",
                "needs_squash": needs_squash_op,
                "needs_submit": needs_submit_op,
            },
        }

        if not output_human:
            click.echo(json.dumps(result, indent=2))
        else:
            # Human readable format
            click.echo(f"Current Branch: {current_branch}")
            click.echo(f"Previous Branch: {previous_branch or 'None'}")
            click.echo(f"PR Number: {pr_number or 'None'}")
            click.echo(f"Repository State: {repo_state}")
            click.echo(f"Changes: {changes_info['diff_summary']}")
            click.echo(f"Files Changed: {changes_info['files_changed']}")
            click.echo(f"Needs Squash: {needs_squash_op}")
            click.echo(f"Needs Submit: {needs_submit_op}")

    except Exception as e:
        click.echo(f"Error analyzing PR context: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    ai_review_analyze()
