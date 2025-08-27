"""Parse gt stack information in machine-friendly formats."""

import json
import subprocess
import sys
from typing import Any

import click


def parse_gt_log_output(output: str) -> list[dict[str, Any]]:
    """Parse the text output from 'gt log' into structured data.

    Args:
        output: The raw text output from 'gt log' command

    Returns:
        List of dictionaries containing branch information
    """
    branches = []
    current_branch = None

    lines = output.strip().split("\n")

    for original_line in lines:
        line = original_line.strip()

        if not line or line.startswith("├") or line.startswith("◯ master"):
            continue

        # Branch line (starts with ◯ or ◉, potentially indented)
        if "◯ " in line or "◉ " in line:
            # Save previous branch if exists
            if current_branch:
                branches.append(current_branch)

            # Find the symbol position and extract the branch line
            if "◉ " in line:
                symbol_pos = line.find("◉ ")
                branch_line = line[symbol_pos + 2 :].strip()
                is_current = True
            else:
                symbol_pos = line.find("◯ ")
                branch_line = line[symbol_pos + 2 :].strip()
                is_current = False

            # Extract branch name (everything before any parentheses or additional info)
            branch_name = branch_line.split(" ")[0]

            # Check for "(current)" indicator
            if "(current)" in branch_line:
                is_current = True
                status_info = "(current)"
            elif "(" in branch_line:
                # Extract status info from parentheses
                status_info = branch_line[branch_line.find("(") : branch_line.find(")") + 1]
            else:
                status_info = ""

            current_branch = {
                "name": branch_name,
                "is_current": is_current,
                "status_info": status_info,
                "pr_number": None,
                "pr_status": None,
                "pr_url": None,
                "last_submit_version": None,
                "commits": [],
                "timestamp": None,
                "depth": 0,  # Will be calculated based on indentation
            }

        # Timestamp line
        elif current_branch and (
            "hours ago" in line
            or "minutes ago" in line
            or "days ago" in line
            or "weeks ago" in line
            or "months ago" in line
        ):
            # Clean up the timestamp by removing the tree characters
            clean_timestamp = line
            # Remove common tree drawing characters
            for char in ["│", "┃", "┣", "┗", "├", "└", "┌", "┐", "┘", "┌"]:
                clean_timestamp = clean_timestamp.replace(char, " ")
            current_branch["timestamp"] = clean_timestamp.strip()

        # PR line (potentially indented)
        elif current_branch and "PR #" in line:
            # Find PR # and parse from there
            pr_start = line.find("PR #")
            pr_line = line[pr_start:]  # "PR #31717 (Draft) absolute import for InstanceRef"

            parts = pr_line.split()
            if len(parts) >= 2:
                pr_number_part = parts[1]  # "#31717"
                if pr_number_part.startswith("#"):
                    current_branch["pr_number"] = int(pr_number_part[1:])

                # Extract PR status (in parentheses)
                if "(" in pr_line and ")" in pr_line:
                    status_start = pr_line.find("(") + 1
                    status_end = pr_line.find(")")
                    current_branch["pr_status"] = pr_line[status_start:status_end]

                    # Extract PR title (after status)
                    title_start = pr_line.find(")") + 1
                    # Skip any spaces that might exist
                    while title_start < len(pr_line) and pr_line[title_start] == " ":
                        title_start += 1
                    current_branch["pr_title"] = pr_line[title_start:].strip()
                else:
                    # No status, title starts after PR number
                    title_start = len("PR #" + pr_number_part + " ")
                    current_branch["pr_title"] = pr_line[title_start:].strip()

        # PR URL line (potentially indented)
        elif current_branch and "https://app.graphite.dev/github/pr/" in line:
            url_start = line.find("https://")
            if url_start >= 0:
                current_branch["pr_url"] = line[url_start:].strip()

        # Submit version line
        elif current_branch and "Last submitted version:" in line:
            # Parse "Last submitted version: v1 (local changes, need submit)"
            version_part = line.split("Last submitted version: ")[1]
            if "(" in version_part:
                version = version_part[: version_part.find("(")].strip()
                extra_info = version_part[
                    version_part.find("(") + 1 : version_part.find(")")
                ].strip()
                current_branch["last_submit_version"] = version
                current_branch["submit_status"] = extra_info
            else:
                current_branch["last_submit_version"] = version_part.strip()
                current_branch["submit_status"] = None

        # Commit line (starts with commit hash)
        elif current_branch and len(line) >= 10 and all(c in "0123456789abcdef" for c in line[:10]):
            # Parse "13da8b273c - absolute import for InstanceRef"
            if " - " in line:
                commit_hash, commit_message = line.split(" - ", 1)
                current_branch["commits"].append(
                    {"hash": commit_hash.strip(), "message": commit_message.strip()}
                )

    # Don't forget the last branch
    if current_branch:
        branches.append(current_branch)

    return branches


@click.command(name="gt-stack")
@click.option(
    "--stack",
    "-s",
    is_flag=True,
    default=False,
    help="Only show ancestors and descendants of current branch",
)
@click.option(
    "--current-only", is_flag=True, default=False, help="Only show the current branch information"
)
def gt_stack(stack: bool, current_only: bool) -> None:
    """Parse gt stack information in machine-friendly JSON format.

    Parses the output of 'gt log' and converts it to structured JSON data
    for easier consumption by scripts and tools.
    """
    try:
        # Build gt log command
        cmd = ["gt", "log"]
        if stack:
            cmd.append("--stack")

        # Run gt log command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse the output
        branches = parse_gt_log_output(output)

        # Filter to current branch only if requested
        if current_only:
            branches = [branch for branch in branches if branch.get("is_current", False)]

        # Output in JSON format
        click.echo(json.dumps(branches, indent=2))

    except subprocess.CalledProcessError as e:
        click.echo(f"Error running gt log: {e.stderr}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error parsing gt output: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    gt_stack()
