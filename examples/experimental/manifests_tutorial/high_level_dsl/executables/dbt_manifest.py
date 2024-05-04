from typing import Any, Literal, Mapping, Optional, Type

from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._manifest.executable import ManifestBackedExecutable
from dagster._manifest.schema import ExecutableManifest
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from pydantic import BaseModel


class DbtManifestJsonExecutableManifest(BaseModel):
    kind: Literal["dbt_manifest"]
    manifest_json_path: str
    group_name: Optional[str] = None


class DbtManifestJsonExecutable(ManifestBackedExecutable):
    @classmethod
    def create_from_manifest(
        cls, manifest: DbtManifestJsonExecutableManifest
    ) -> "DbtManifestJsonExecutable":
        return DbtManifestJsonExecutable(
            manifest=manifest,
            # we override to_assets_def so we don't need this
            # TODO. change class hierarchy to allow for this use case
            specs=[],
        )

    def to_assets_def(self) -> AssetsDefinition:
        manifest = self.manifest

        class _Translater(DagsterDbtTranslator):
            def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
                return manifest.group_name

            ...

        @dbt_assets(manifest=self.manifest.manifest_json_path, dagster_dbt_translator=_Translater())
        def _dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
            dbt_build_invocation = dbt.cli(["build"], context=context)
            yield from dbt_build_invocation.stream()

        return _dbt_assets

    def execute(
        self, context: AssetGraphExecutionContext, dbt: DbtCliResource
    ) -> AssetGraphExecutionResult:
        raise NotImplementedError("This should never be called")

    @classmethod
    def manifest_cls(cls) -> Optional[Type[ExecutableManifest]]:
        return DbtManifestJsonExecutableManifest
