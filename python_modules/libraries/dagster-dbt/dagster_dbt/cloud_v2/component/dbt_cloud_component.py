from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, Model, Resolvable
from dagster_dbt.cloud_v2.asset_decorator import (
    DBT_CLOUD_DEFAULT_EXCLUDE,
    DBT_CLOUD_DEFAULT_SELECT,
    DBT_CLOUD_DEFAULT_SELECTOR,
    dbt_cloud_assets,
)
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.components.dbt_project.component import (
    DagsterDbtComponentsTranslatorSettings,
    ProxyDagsterDbtTranslator,
    ResolvedTranslationFn,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_shared import check


class DbtCloudComponent(Component, Resolvable, Model):
    name: str
    group_name: Optional[str] = None
    select: str = DBT_CLOUD_DEFAULT_SELECT
    exclude: str = DBT_CLOUD_DEFAULT_EXCLUDE
    selector: str = DBT_CLOUD_DEFAULT_SELECTOR

    translation: Optional[ResolvedTranslationFn] = None
    translation_settings: Optional[DagsterDbtComponentsTranslatorSettings] = None

    @cached_property
    def translator(self):
        translation_settings = self.translation_settings or DagsterDbtComponentsTranslatorSettings()
        if self.translation:
            return ProxyDagsterDbtTranslator(self.translation, translation_settings)
        return DagsterDbtTranslator(translation_settings)

    def build_defs(
        self,
        context: ComponentLoadContext,
    ) -> dg.Definitions:
        check.invariant(
            "dbt_cloud_workspace" in context.resources,
            f"dbt_cloud_workspace is required to load dbt cloud assets. Has resources: {list(context.resources.keys())}",
        )

        # this should probably fetch things lazily
        dbt_cloud_workspace = check.inst(
            context.resources["dbt_cloud_workspace"],
            DbtCloudWorkspace,
            "dbt_cloud_workspace must be a DbtCloudWorkspace",
        )

        @dbt_cloud_assets(
            workspace=dbt_cloud_workspace,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            name=self.name,
            group_name=self.group_name,
        )
        def _fn(context: AssetExecutionContext): ...

        return dg.Definitions(assets=[_fn])
