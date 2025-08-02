"""Submit summarized PR command group with subcommands."""

import sys

import click

from automation.dagster_claude_commands.utils.git_operations import (
    amend_commit_message,
    get_commit_messages_since_ref,
    get_diff_since_ref,
)
from automation.dagster_claude_commands.utils.github_operations import (
    get_current_pr_url,
    update_pr_title_and_body,
)
from automation.dagster_claude_commands.utils.graphite_operations import (
    get_stack_base,
    squash_branch,
    submit_draft_pr,
)
from automation.dagster_claude_commands.utils.pr_summary import (
    extract_title_from_summary,
    generate_pr_summary,
)
from automation.dagster_claude_commands.utils.validation import (
    check_has_commits_to_squash,
    validate_prerequisites,
)


@click.group("submit-summarized-pr")
def submit_summarized_pr():
    """Submit PR with AI-generated summary - command group."""
    pass


@submit_summarized_pr.command("submit")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing operations"
)
@click.option(
    "--no-squash", is_flag=True, help="Skip squashing commits (useful if already squashed)"
)
def submit(dry_run: bool, no_squash: bool):
    """Submit a PR with AI-generated summary by squashing branch and creating draft PR.

    This command performs the following steps:
    1. Validates prerequisites (git repo, CLI tools, branch status)
    2. Squashes commits in the current branch (unless --no-squash)
    3. Generates PR summary from commit messages and diff
    4. Amends commit with the generated summary
    5. Creates/updates draft PR using Graphite
    6. Updates PR title and body using GitHub CLI
    """
    try:
        click.echo("🔍 Validating prerequisites...")
        if not dry_run:
            validate_prerequisites()
        else:
            click.echo("  [DRY RUN] Would validate git repo, CLI tools, and branch status")

        click.echo("\\n📊 Gathering context...")

        # Get stack base
        stack_base = get_stack_base()
        if not stack_base:
            click.echo("Error: Could not determine Graphite stack base", err=True)
            sys.exit(1)

        click.echo(f"  Stack base: {stack_base}")

        # Get commit messages and diff
        commit_messages = get_commit_messages_since_ref(stack_base)
        diff_content = get_diff_since_ref(stack_base)

        if not commit_messages.strip():
            click.echo("Error: No commits found since stack base. Nothing to submit.", err=True)
            sys.exit(1)

        click.echo(f"  Found {len(commit_messages.split(chr(10)))} commits")
        click.echo(f"  Diff size: {len(diff_content)} characters")

        # Step 1: Squash commits (if needed and not skipped)
        if not no_squash:
            click.echo("\\n🔄 Squashing commits...")
            if dry_run:
                has_commits = check_has_commits_to_squash()
                if has_commits:
                    click.echo("  [DRY RUN] Would squash multiple commits")
                else:
                    click.echo("  [DRY RUN] Single commit, nothing to squash")
            else:
                if not squash_branch():
                    click.echo("Error: Failed to squash commits", err=True)
                    sys.exit(1)
        else:
            click.echo("\\n⏭️  Skipping commit squashing (--no-squash)")

        # Step 2: Generate PR summary
        click.echo("\\n✨ Generating PR summary...")
        if dry_run:
            click.echo("  [DRY RUN] Would generate summary from commit messages and diff")
            pr_summary = "## Summary & Motivation\\n\\nDry run summary\\n\\n## How I Tested These Changes\\n\\nDry run testing\\n\\n## Changelog\\n\\nDry run changelog"
        else:
            pr_summary = generate_pr_summary(commit_messages, diff_content)

        # Extract title from summary
        pr_title = extract_title_from_summary(pr_summary)
        click.echo(f"  Generated title: {pr_title}")

        # Step 3: Amend commit with summary
        click.echo("\\n📝 Updating commit message...")
        if dry_run:
            click.echo("  [DRY RUN] Would amend commit with generated summary")
        else:
            if not amend_commit_message(pr_summary):
                click.echo("Error: Failed to amend commit message", err=True)
                sys.exit(1)

        # Step 4: Submit draft PR
        click.echo("\\n🚀 Creating/updating draft PR...")
        if dry_run:
            click.echo("  [DRY RUN] Would create/update draft PR using Graphite")
            pr_url = "https://github.com/example/repo/pull/123"
        else:
            pr_url = submit_draft_pr()
            if not pr_url:
                # Try to get existing PR URL
                pr_url = get_current_pr_url()
                if not pr_url:
                    click.echo(
                        "Warning: Could not determine PR URL, but draft may have been created"
                    )

        # Step 5: Update PR title and body
        if pr_url:
            click.echo("\\n📋 Updating PR title and body...")
            if dry_run:
                click.echo(f"  [DRY RUN] Would update PR {pr_url}")
                click.echo(f"  [DRY RUN] Title: {pr_title}")
                click.echo(f"  [DRY RUN] Body: {len(pr_summary)} characters")
            else:
                if not update_pr_title_and_body(pr_url, pr_title, pr_summary):
                    click.echo("Warning: Failed to update PR title/body, but draft PR was created")

        # Success message
        click.echo("\\n✅ Successfully completed submit-summarized-pr workflow!")
        if pr_url:
            click.echo(f"   PR URL: {pr_url}")

        if dry_run:
            click.echo("\\n💡 Run without --dry-run to execute the workflow")

    except KeyboardInterrupt:
        click.echo("\\n\\n⚠️  Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@submit_summarized_pr.command("print-pr-summary")
def print_pr_summary():
    """Print PR summary to stdout for testing purposes.

    This command generates a PR summary using the same logic as submit
    but outputs it to stdout instead of creating a PR. Useful for testing the
    summary generation without side effects.
    """
    try:
        click.echo("🔍 Validating prerequisites...")
        validate_prerequisites()

        click.echo("📊 Gathering context...")

        # Get stack base
        stack_base = get_stack_base()
        if not stack_base:
            click.echo("Error: Could not determine Graphite stack base", err=True)
            sys.exit(1)

        click.echo(f"  Stack base: {stack_base}")

        # Get commit messages and diff
        commit_messages = get_commit_messages_since_ref(stack_base)
        diff_content = get_diff_since_ref(stack_base)

        if not commit_messages.strip():
            click.echo("Error: No commits found since stack base. Nothing to summarize.", err=True)
            sys.exit(1)

        click.echo(f"  Found {len(commit_messages.split(chr(10)))} commits")
        click.echo(f"  Diff size: {len(diff_content)} characters")

        # Generate PR summary
        click.echo("\\n✨ Generating PR summary...")
        pr_summary = generate_pr_summary(commit_messages, diff_content)

        # Output the summary
        click.echo("\\n" + "=" * 50)
        click.echo("Generated PR Summary:")
        click.echo("=" * 50)
        click.echo(pr_summary)
        click.echo("=" * 50)

    except KeyboardInterrupt:
        click.echo("\\n\\n⚠️  Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@submit_summarized_pr.command("print-pr-title")
def print_pr_title():
    """Print PR title to stdout for testing title generation.

    This command generates a PR title using the same logic as submit
    but outputs only the title to stdout. Useful for testing the
    title generation without side effects.
    """
    try:
        click.echo("🔍 Validating prerequisites...")
        validate_prerequisites()

        click.echo("📊 Gathering context...")

        # Get stack base
        stack_base = get_stack_base()
        if not stack_base:
            click.echo("Error: Could not determine Graphite stack base", err=True)
            sys.exit(1)

        click.echo(f"  Stack base: {stack_base}")

        # Get commit messages and diff
        commit_messages = get_commit_messages_since_ref(stack_base)
        diff_content = get_diff_since_ref(stack_base)

        if not commit_messages.strip():
            click.echo(
                "Error: No commits found since stack base. Nothing to generate title for.", err=True
            )
            sys.exit(1)

        click.echo(f"  Found {len(commit_messages.split(chr(10)))} commits")
        click.echo(f"  Diff size: {len(diff_content)} characters")

        # Generate PR summary
        click.echo("\\n✨ Generating PR summary...")
        pr_summary = generate_pr_summary(commit_messages, diff_content)

        # Extract title from summary
        click.echo("\\n🏷️  Generating PR title...")
        pr_title = extract_title_from_summary(pr_summary)

        # Output the title
        click.echo("\\n" + "=" * 50)
        click.echo("Generated PR Title:")
        click.echo("=" * 50)
        click.echo(pr_title)
        click.echo("=" * 50)
        click.echo(f"Title length: {len(pr_title)} characters")

    except KeyboardInterrupt:
        click.echo("\\n\\n⚠️  Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)
