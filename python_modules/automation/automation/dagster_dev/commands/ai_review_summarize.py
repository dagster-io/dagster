"""Smart diff summarization command for AI code review."""

import json
import sys

import click

from automation.dagster_dev.commands.diff_summarizer import (
    format_summary_for_ai,
    get_smart_diff_summary,
)


@click.command(name="ai-review-summarize")
@click.option(
    "--diff-range",
    default="master..HEAD",
    help="Git diff range to analyze (default: master..HEAD)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "human"], case_sensitive=False),
    default="json",
    help="Output format for the summary",
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.7,
    help="Minimum confidence threshold for summary (0.0-1.0)",
)
def ai_review_summarize(diff_range: str, output_format: str, confidence_threshold: float) -> None:
    """Generate smart diff summary optimized for AI code analysis.

    This command analyzes code changes using intelligent categorization and structural
    analysis, providing semantic understanding without processing full diff content.

    The summary includes:
    - Change categorization (feature, bugfix, refactor, etc.)
    - Structural changes (functions, classes, imports)
    - Focused implementation details when relevant
    - API impact assessment
    - Confidence metrics for analysis quality

    Examples:
        # Analyze current branch changes
        dagster-dev ai-review-summarize

        # Analyze specific diff range
        dagster-dev ai-review-summarize --diff-range=main..feature-branch

        # Get human-readable output
        dagster-dev ai-review-summarize --format=human

        # Only show high-confidence summaries
        dagster-dev ai-review-summarize --confidence-threshold=0.9
    """
    try:
        click.echo(f"🔍 Analyzing changes in range: {diff_range}")

        # Generate smart summary
        summary = get_smart_diff_summary(diff_range)

        # Check confidence threshold
        if summary.summary_confidence < confidence_threshold:
            click.echo(
                f"⚠️  Summary confidence ({summary.summary_confidence:.2f}) below threshold "
                f"({confidence_threshold}). Consider using full diff analysis.",
                err=True,
            )
            if output_format == "json":
                # Still output JSON but with warning metadata
                result = format_summary_for_ai(summary)
                result["warnings"] = [f"Low confidence: {summary.summary_confidence:.2f}"]
                click.echo(json.dumps(result, indent=2))
                return

        if output_format == "json":
            # Machine-readable output for AI consumption
            result = format_summary_for_ai(summary)
            click.echo(json.dumps(result, indent=2))

        else:
            # Human-readable output
            click.echo("\n📋 Change Summary")
            click.echo(
                f"Scope: {summary.files_changed} files, +{summary.additions}/-{summary.deletions} lines"
            )
            click.echo(f"Confidence: {summary.summary_confidence:.1%}")

            if summary.functions:
                click.echo("\n🔧 Function Changes:")
                for func in summary.functions[:10]:  # Limit display
                    click.echo(f"  • {func.details}")

            if summary.classes:
                click.echo("\n📦 Class Changes:")
                for cls in summary.classes[:5]:
                    click.echo(f"  • {cls.details}")

            if summary.imports:
                click.echo("\n📥 Import Changes:")
                for imp in summary.imports[:8]:
                    click.echo(f"  • {imp.details}")

            if summary.api_changes:
                click.echo("\n🔗 API Impact:")
                for change in summary.api_changes:
                    click.echo(f"  • {change}")

            if summary.key_implementation_details:
                click.echo("\n💡 Key Implementation Details:")
                # Show first few lines of details
                details_lines = summary.key_implementation_details.split("\n")[:8]
                for line in details_lines:
                    if line.strip():
                        click.echo(f"  {line}")
                if len(summary.key_implementation_details.split("\n")) > 8:
                    click.echo("  ... (truncated)")

    except ValueError as e:
        click.echo(f"❌ Error analyzing diff: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    ai_review_summarize()
