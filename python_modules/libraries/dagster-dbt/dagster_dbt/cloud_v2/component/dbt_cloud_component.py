from collections.abc import Iterator
from dataclasses import replace
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Optional, cast

import dagster as dg
from dagster import AssetExecutionContext, Definitions, multi_asset
from dagster._annotations import public
from dagster.components import ComponentLoadContext
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs
from dagster_shared.serdes import deserialize_value, serialize_value
from pydantic import Field

from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
)
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.components.dbt_component_utils import (
    DagsterDbtComponentTranslatorSettings,
    _set_resolution_context,
    build_op_spec,
    resolve_cli_args,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest import validate_manifest

if TYPE_CHECKING:
    from dagster_dbt.cloud_v2.types import DbtCloudWorkspaceData


def resolve_workspace(context: ResolutionContext, model: Any) -> DbtCloudWorkspace:
    """Resolves the DbtCloudWorkspace from the component configuration."""
    resolved_val = context.resolve_value(model)
    if isinstance(resolved_val, DbtCloudWorkspace):
        return resolved_val
    return DbtCloudWorkspace(**resolved_val)


@public
class DbtCloudComponent(StateBackedComponent, dg.Resolvable, dg.Model):
    """Expose a dbt Cloud workspace to Dagster as a set of assets."""

    model_config = {"arbitrary_types_allowed": True}

    workspace: Annotated[
        DbtCloudWorkspace,
        Resolver(
            fn=resolve_workspace,
            description="The dbt Cloud workspace resource to use for this component.",
        ),
    ]

    cli_args: Annotated[
        list[str | dict[str, Any]],
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

    defs_state: Annotated[
        DefsStateConfigArgs,
        Resolver.passthrough(
            description="Configuration for how definitions state should be managed.",
        ),
    ] = Field(default_factory=DefsStateConfigArgs.local_filesystem)

    @property
    def defs_state_config(self) -> DefsStateConfig:
        key = f"DbtCloudComponent[{self.workspace.unique_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=key)

    @cached_property
    def translator(self) -> DagsterDbtTranslator:
        settings = replace(self.translation_settings, enable_code_references=False)
        return DagsterDbtTranslator(settings)

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:
        return None

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:
        return self.op_config_schema

    def _get_op_spec(self, op_name: str = "dbt_cloud_assets") -> OpSpec:
        return build_op_spec(
            op=self.op,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            op_name=op_name,
        )

    def get_cli_args(self, context: AssetExecutionContext) -> list[str]:
        return resolve_cli_args(self.cli_args, context)

    def write_state_to_path(self, state_path: Path) -> None:
        workspace_data = self.workspace.fetch_workspace_data()
        state_path.write_text(serialize_value(workspace_data))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> Definitions:
        if state_path is None:
            return Definitions()

        workspace_data = cast("DbtCloudWorkspaceData", deserialize_value(state_path.read_text()))
        manifest = workspace_data.manifest
        res_ctx = context.resolution_context

        asset_specs, check_specs = build_dbt_specs(
            translator=self.translator,
            manifest=validate_manifest(manifest),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=None,
            io_manager_key=None,
        )

        op_spec = self._get_op_spec("dbt_cloud_assets")

        @multi_asset(
            specs=asset_specs,
            check_specs=check_specs,
            can_subset=True,
            name=op_spec.name,
            op_tags=op_spec.tags,
            backfill_policy=op_spec.backfill_policy,
            pool=op_spec.pool,
            config_schema=self.config_cls.to_fields_dict() if self.config_cls else None,
            allow_arbitrary_check_specs=self.translator.settings.enable_source_tests_as_checks,
        )
        def _dbt_cloud_assets(context: AssetExecutionContext) -> Iterator:
            with _set_resolution_context(res_ctx):
                yield from self.execute(context=context)

        return Definitions(assets=[_dbt_cloud_assets])

    def execute(self, context: AssetExecutionContext) -> Iterator:
        invocation = self.workspace.cli(
            args=self.get_cli_args(context),
            dagster_dbt_translator=self.translator,
            context=context,
        )
        yield from invocation.wait()
