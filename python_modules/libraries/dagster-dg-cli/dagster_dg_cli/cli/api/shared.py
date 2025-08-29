"""Shared utilities for API commands."""

import click
from dagster_shared.plus.config import DagsterPlusCliConfig


def get_config_or_error() -> DagsterPlusCliConfig:
    """Get Dagster Plus config or raise error if not authenticated."""
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg api` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()
