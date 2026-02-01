import itertools
import json
from abc import ABC
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cached_property
from typing import Annotated, Any, Optional, Union

import dagster as dg
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster_shared import check
from pydantic import Field

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings

_resolution_context: ContextVar[ResolutionContext] = ContextVar("resolution_context")


@contextmanager
def _set_resolution_context(context: ResolutionContext):
    """Context manager to set the resolution context for dbt components."""
    token = _resolution_context.set(context)
    try:
        yield
    finally:
        _resolution_context.reset(token)


class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


class BaseDbtComponent(StateBackedComponent, dg.Resolvable, dg.Model, ABC):
    """Base class for dbt components (both local and cloud)."""

    model_config = {"arbitrary_types_allowed": True}

    cli_args: Annotated[
        list[Union[str, dict[str, Any]]],
        Resolver.passthrough(
            description="Arguments to pass to the dbt CLI when executing. Defaults to `['build']`.",
            examples=[
                ["run"],
                [
                    "build",
                    "--full_refresh",
                    {
                        "--vars": {
                            "start_date": "{{ partition_range_start }}",
                            "end_date": "{{ partition_range_end }}",
                        },
                    },
                ],
            ],
        ),
    ] = Field(default_factory=lambda: ["build"])

    op: Annotated[
        Optional[OpSpec],
        Resolver.default(
            description="Op related arguments to set on the generated @dbt_assets",
            examples=[
                {
                    "name": "some_op",
                    "tags": {"tag1": "value"},
                    "backfill_policy": {"type": "single_run"},
                },
            ],
        ),
    ] = None

    select: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models you want to include.",
            examples=["tag:dagster"],
        ),
    ] = DBT_DEFAULT_SELECT

    exclude: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models you want to exclude.",
            examples=["tag:skip_dagster"],
        ),
    ] = DBT_DEFAULT_EXCLUDE

    selector: Annotated[
        str,
        Resolver.default(
            description="The dbt selector for models you want to include.",
            examples=["custom_selector"],
        ),
    ] = DBT_DEFAULT_SELECTOR

    translation_settings: DagsterDbtComponentTranslatorSettings = Field(
        default_factory=DagsterDbtComponentTranslatorSettings,
        description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
        examples=[
            {
                "enable_source_tests_as_checks": True,
            },
        ],
    )

    @cached_property
    def translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator(self.translation_settings)

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:
        return None

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:
        return self.op_config_schema

    def _get_op_spec(self, op_name: Optional[str] = None) -> OpSpec:
        if op_name is None:
            op_name = "dbt_assets"

        default = self.op or OpSpec(name=op_name)
        return default.model_copy(
            update=dict(
                tags={
                    **(default.tags or {}),
                    **({DAGSTER_DBT_SELECT_METADATA_KEY: self.select} if self.select else {}),
                    **({DAGSTER_DBT_EXCLUDE_METADATA_KEY: self.exclude} if self.exclude else {}),
                    **({DAGSTER_DBT_SELECTOR_METADATA_KEY: self.selector} if self.selector else {}),
                }
            )
        )

    def get_cli_args(self, context: dg.AssetExecutionContext) -> list[str]:
        partition_key = context.partition_key if context.has_partition_key else None
        partition_key_range = (
            context.partition_key_range if context.has_partition_key_range else None
        )
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
            .resolve_value(self.cli_args, as_type=list[str])
        )

        def _normalize_arg(arg: Union[str, dict[str, Any]]) -> list[str]:
            if isinstance(arg, str):
                return [arg]

            check.invariant(
                len(arg.keys()) == 1, "Invalid cli args dict, must have exactly one key"
            )
            key = next(iter(arg.keys()))
            value = arg[key]
            if isinstance(value, dict):
                normalized_value = json.dumps(value)
            else:
                normalized_value = str(value)

            return [key, normalized_value]

        normalized_args = list(
            itertools.chain(*[list(_normalize_arg(arg)) for arg in resolved_args])
        )
        return normalized_args

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[Any] = None
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node using the configured translator."""
        return self.translator.get_asset_spec(manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional[Any] = None,
    ) -> Optional[dg.AssetCheckSpec]:
        return self.translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)
