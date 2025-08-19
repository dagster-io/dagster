"""Cache management command for AI code review analysis."""

import json
import sys

import click

from automation.dagster_dev.commands.cache_manager import CacheManager


@click.command(name="ai-review-cache")
@click.option(
    "--action",
    type=click.Choice(["status", "clear"], case_sensitive=False),
    default="status",
    help="Cache management action to perform",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "human"], case_sensitive=False),
    default="human",
    help="Output format for cache information",
)
def ai_review_cache(action: str, output_format: str) -> None:
    """Manage cache for AI code review analysis.

    This command provides cache management capabilities for the AI code review
    system, including status checking and cache clearing operations.

    The cache stores analysis results to avoid re-processing the same repository
    state, significantly reducing costs and improving performance for repeated
    AI review operations.

    Examples:
        # Check cache status
        dagster-dev ai-review-cache --action=status

        # Clear all cached data
        dagster-dev ai-review-cache --action=clear

        # Get cache status in JSON format
        dagster-dev ai-review-cache --action=status --format=json
    """
    try:
        cache_manager = CacheManager()

        if action == "status":
            status = cache_manager.get_cache_status()

            if output_format == "json":
                click.echo(json.dumps(status, indent=2))
            else:
                click.echo("📊 AI Review Cache Status")

                if not status["exists"]:
                    click.echo("   No cache found")
                elif status.get("error"):
                    click.echo(f"   ❌ Error: {status['error']}")
                else:
                    click.echo(f"   Cache size: {status['size_bytes']:,} bytes")
                    click.echo(f"   Entries: {status['entries']}")

                    if status["entries"] > 0:
                        import time

                        last_time = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(status["last_analysis"])
                        )
                        click.echo(f"   Last analysis: {last_time}")
                        click.echo(f"   Cached commit: {status['cached_commit']}")
                        click.echo(f"   Cached branch: {status['cached_branch']}")
                        click.echo(
                            f"   Valid: {'✅ Yes' if status['is_valid'] else '❌ No (stale)'}"
                        )

        elif action == "clear":
            if cache_manager.clear_cache():
                click.echo("✅ Cache cleared successfully")
            else:
                click.echo("❌ Failed to clear cache", err=True)
                sys.exit(1)

    except ValueError as e:
        if "Not in a git repository" in str(e):
            click.echo("❌ Error: Must be run from within a git repository", err=True)
        else:
            click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    ai_review_cache()
