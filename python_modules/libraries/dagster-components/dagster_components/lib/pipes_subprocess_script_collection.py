import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from pydantic import BaseModel, ConfigDict

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    registered_component_type,
)
from dagster_components.core.schema.base import ResolvableSchema, field_resolver
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.objects import AssetSpecSchema

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class PipesSubprocessScriptSpec(BaseModel):
    path: str
    assets: Sequence[AssetSpec]

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)


class PipesSubprocessScriptParams(ResolvableSchema[PipesSubprocessScriptSpec]):
    path: str
    assets: Sequence[AssetSpecSchema]


class PipesSubprocessScriptCollectionParams(ResolvableSchema["PipesSubprocessScriptCollection"]):
    scripts: Sequence[PipesSubprocessScriptParams]


@registered_component_type(name="pipes_subprocess_script_collection")
class PipesSubprocessScriptCollection(Component):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    specs_by_path: Mapping[str, Sequence[AssetSpec]]

    @staticmethod
    @field_resolver("specs_by_path")
    def resolve_specs_by_path(
        schema: PipesSubprocessScriptCollectionParams, context: ResolutionContext
    ) -> Mapping[str, Sequence[AssetSpec]]:
        return {spec.path: spec.assets for spec in context.resolve_value(schema.scripts)}

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollection":
        path_specs = {str(path): [AssetSpec(path.stem)] for path in list(path.rglob("*.py"))}
        return PipesSubprocessScriptCollection(specs_by_path=path_specs)

    @classmethod
    def get_schema(cls) -> type[PipesSubprocessScriptCollectionParams]:
        return PipesSubprocessScriptCollectionParams

    def build_defs(self, context: "ComponentLoadContext") -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions(
            assets=[
                self._create_asset_def(context.path / path, specs)
                for path, specs in self.specs_by_path.items()
            ],
        )

    def _create_asset_def(self, path: Path, specs: Sequence[AssetSpec]) -> AssetsDefinition:
        # TODO: allow name paraeterization
        @multi_asset(specs=specs, name=f"script_{path.stem}")
        def _asset(context: AssetExecutionContext):
            cmd = [shutil.which("python"), path]
            return PipesSubprocessClient().run(command=cmd, context=context).get_results()

        return _asset
