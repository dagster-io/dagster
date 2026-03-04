"""Shared utilities for API commands."""

import contextlib
import json
from collections.abc import Iterator

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.api.client import DgApiTestContext


@contextlib.contextmanager
def handle_api_errors(ctx: click.Context, output_json: bool = False) -> Iterator[None]:
    """Context manager for uniform API error handling.

    Derives the operation name from ``ctx.command_path`` (e.g. ``"dg api agent list"``).
    Re-raises ClickExceptions as-is. For all other exceptions, emits a JSON error
    object to stderr when ``output_json`` is True, then raises a ClickException.
    """
    try:
        yield
    except click.ClickException:
        raise
    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}), err=True)
        raise click.ClickException(f"{ctx.command_path}: {e}")


def get_config_or_error() -> DagsterPlusCliConfig:
    """Get Dagster Plus config or raise error if not authenticated."""
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg api` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def get_config_for_api_command(ctx: click.Context) -> DagsterPlusCliConfig:
    """Get config for API commands, supporting both test and normal contexts."""
    # Check if we're in a test context
    if ctx.obj and isinstance(ctx.obj, DgApiTestContext):
        # Return a mock config for testing
        return DagsterPlusCliConfig(
            organization=ctx.obj.organization,
            default_deployment=ctx.obj.deployment,
            user_token="test-token",  # Mock token for testing
        )

    # Normal operation - use existing authentication logic
    return get_config_or_error()
