"""Shared utilities for dbt components (both local project and cloud)."""

import itertools
import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional, Union

import dagster as dg
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster_shared import check

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslatorSettings

_resolution_context: ContextVar[ResolutionContext] = ContextVar("resolution_context")


@contextmanager
def _set_resolution_context(context: ResolutionContext):
    """Context manager to set the resolution context for dbt components."""
    token = _resolution_context.set(context)
    try:
        yield
    finally:
        _resolution_context.reset(token)


@dataclass(frozen=True)
class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


def build_op_spec(
    op: Optional[OpSpec],
    select: str,
    exclude: str,
    selector: str,
    op_name: str,
) -> OpSpec:
    """Build an OpSpec with dbt selection tags injected."""
    default = op or OpSpec(name=op_name)
    return default.model_copy(
        update=dict(
            tags={
                **(default.tags or {}),
                **({DAGSTER_DBT_SELECT_METADATA_KEY: select} if select else {}),
                **({DAGSTER_DBT_EXCLUDE_METADATA_KEY: exclude} if exclude else {}),
                **({DAGSTER_DBT_SELECTOR_METADATA_KEY: selector} if selector else {}),
            }
        )
    )


def resolve_cli_args(
    cli_args: list[Union[str, dict[str, Any]]],
    context: dg.AssetExecutionContext,
) -> list[str]:
    """Resolve and normalize CLI args using the current resolution context and partition scope."""
    partition_key = context.partition_key if context.has_partition_key else None
    partition_key_range = context.partition_key_range if context.has_partition_key_range else None
    try:
        partition_time_window = context.partition_time_window
    except Exception:
        partition_time_window = None

    resolved_args = (
        _resolution_context.get()
        .with_scope(
            partition_key=partition_key,
            partition_key_range=partition_key_range,
            partition_time_window=partition_time_window,
        )
        .resolve_value(cli_args, as_type=list[str])
    )

    def _normalize_arg(arg: Union[str, dict[str, Any]]) -> list[str]:
        if isinstance(arg, str):
            return [arg]

        check.invariant(len(arg.keys()) == 1, "Invalid cli args dict, must have exactly one key")
        key = next(iter(arg.keys()))
        value = arg[key]
        if isinstance(value, dict):
            normalized_value = json.dumps(value)
        else:
            normalized_value = str(value)

        return [key, normalized_value]

    normalized_args = list(itertools.chain(*[list(_normalize_arg(arg)) for arg in resolved_args]))
    return normalized_args
