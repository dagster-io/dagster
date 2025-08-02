"""PR summary generation utilities for dagster-claude-commands."""

import os
import subprocess


def generate_pr_summary(commit_messages: str, diff_content: str) -> str:
    """Generate PR summary using Claude CLI following the template format.

    Args:
        commit_messages: Git commit messages since base ref
        diff_content: Git diff content since base ref

    Returns:
        Generated PR summary in markdown format
    """
    try:
        # Read the PR summary template - find it relative to this file
        # Navigate from this file to the repo root and then to the template
        current_file_dir = os.path.dirname(__file__)
        repo_root = os.path.join(current_file_dir, "..", "..", "..", "..", "..")
        template_path = os.path.join(repo_root, ".claude", "templates", "pr_summary_template.md")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"PR summary template not found at {template_path}")

        with open(template_path) as f:
            template_content = f.read()

        # Prepare the prompt for Claude CLI using the template
        prompt = f"""{template_content}

Here is the context for generating the PR summary:

## Commit Messages:
{commit_messages}

## Diff Content:
{diff_content[:5000]}{"...(truncated)" if len(diff_content) > 5000 else ""}

Generate the PR summary following the template format exactly. Only return the markdown content starting with "## Summary & Motivation"."""

        # Invoke Claude CLI to generate the summary
        result = subprocess.run(
            ["claude", "--print", prompt], capture_output=True, text=True, timeout=120, check=False
        )

        if result.returncode == 0:
            # Extract just the markdown content from Claude's response
            response = result.stdout.strip()
            # Look for the actual summary content (after any preamble)
            if "## Summary & Motivation" in response:
                # Find the start of the actual summary
                start_idx = response.find("## Summary & Motivation")
                return response[start_idx:].strip()
            else:
                return response.strip()
        else:
            raise RuntimeError(
                f"Claude CLI failed with return code {result.returncode}: {result.stderr}"
            )

    except Exception as e:
        raise RuntimeError(f"Failed to generate PR summary using Claude CLI: {e}")


def extract_title_from_summary(summary: str) -> str:
    """Generate a concise PR title using Claude CLI."""
    title_prompt = f"""You are a GitHub PR title generator. Create a concise, professional PR title based on the summary below.

Requirements:
- Maximum 50 characters
- Use imperative mood (e.g., "Add", "Fix", "Implement", "Update")  
- Be specific about what changed
- Avoid vague words like "change", "modify", "improve" unless necessary
- Focus on the primary feature/fix/change
- No quotes, periods, or ellipsis

Examples of good titles:
- "Add CLI command for PR automation"
- "Fix memory leak in asset processing"
- "Implement OAuth2 authentication"
- "Update GraphQL schema validation"

PR Summary:
{summary[:1500]}

Generate only the title text, nothing else."""

    result = subprocess.run(
        ["claude", "--print", title_prompt], capture_output=True, text=True, timeout=30, check=True
    )

    generated_title = result.stdout.strip()
    # Clean up the title - remove quotes if present
    generated_title = generated_title.strip("\"'")

    if not generated_title:
        raise RuntimeError("Claude CLI returned empty title")

    return generated_title
