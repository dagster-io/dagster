from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Optional, cast

from dagster import AssetExecutionContext, Definitions, multi_asset
from dagster._annotations import public
from dagster.components import ComponentLoadContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs
from dagster_shared.serdes import deserialize_value, serialize_value
from pydantic import Field

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.components.base import BaseDbtComponent, _set_resolution_context
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
class DbtCloudComponent(BaseDbtComponent):
    """Expose a dbt Cloud workspace to Dagster as a set of assets."""

    workspace: Annotated[
        DbtCloudWorkspace,
        Resolver(
            fn=resolve_workspace,
            description="The dbt Cloud workspace resource to use for this component.",
        ),
    ]

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

    @property
    def translator(self) -> DagsterDbtTranslator:
        settings = replace(self.translation_settings, enable_code_references=False)
        return DagsterDbtTranslator(settings)

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
