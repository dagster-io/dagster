import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional

import dagster as dg
from dagster._annotations import public
from dagster._utils.cached_method import cached_method
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs, ResolvedDefsStateConfig

from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    build_dbt_specs,
)
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.components.base import BaseDbtComponent
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import validate_manifest


def resolve_workspace(context: ResolutionContext, model: Any) -> DbtCloudWorkspace:
    """Resolves the DbtCloudWorkspace from the component configuration."""
    resolved_val = context.resolve_value(model)
    if isinstance(resolved_val, DbtCloudWorkspace):
        return resolved_val
    return DbtCloudWorkspace(**resolved_val)


@public
@dataclass(kw_only=True)
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
        ResolvedDefsStateConfig,
        Resolver.passthrough(
            description="Configuration for how definitions state should be managed.",
        ),
    ] = field(default_factory=DefsStateConfigArgs.local_filesystem)

    @property
    def defs_state_config(self) -> DefsStateConfig:
        key = f"DbtCloudComponent[{self.workspace.unique_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=key)

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:
        return None

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:
        return self.op_config_schema

    @property
    @cached_method
    def translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator(self.translation_settings)

    def write_state_to_path(self, state_path: Path) -> None:
        workspace_data = self.workspace.fetch_workspace_data()
        state_data = {
            "project_id": workspace_data.project_id,
            "environment_id": workspace_data.environment_id,
            "adhoc_job_id": workspace_data.adhoc_job_id,
            "manifest": workspace_data.manifest,
            "jobs": [job.__dict__ for job in workspace_data.jobs],
        }
        state_path.write_text(json.dumps(state_data, default=str))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state_data = json.loads(state_path.read_text())
        manifest = state_data["manifest"]

        asset_specs, check_specs = build_dbt_specs(
            translator=validate_translator(self.translator),
            manifest=validate_manifest(manifest),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=None,
            io_manager_key=None,
        )

        op_spec = self._get_op_spec("dbt_cloud_assets")

        @dg.multi_asset(
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
        def _dbt_cloud_assets(context: dg.AssetExecutionContext) -> Iterator:
            yield from self.execute(context=context)

        return dg.Definitions(assets=[_dbt_cloud_assets])

    def execute(self, context: dg.AssetExecutionContext) -> Iterator:
        invocation = self.workspace.cli(
            args=["run"],
            dagster_dbt_translator=self.translator,
            context=context,
        )

        yield from invocation.wait()

    def get_asset_selection(
        self,
        select: str,
        exclude: str = DBT_DEFAULT_EXCLUDE,
        manifest_path: Optional[str] = None,
    ):
        from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection

        workspace_data = self.workspace.fetch_workspace_data()
        manifest = workspace_data.manifest

        return DbtManifestAssetSelection.build(
            manifest=manifest,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )