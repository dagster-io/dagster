import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from pydantic import BaseModel, ConfigDict

from dagster_components import FieldResolver
from dagster_components.core.component import Component, ComponentLoadContext
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.objects import AssetSpecSchema, resolve_asset_spec_schema

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def resolve_assets(
    context: ResolutionContext, schema: "PipesSubprocessScriptSchema"
) -> Sequence[AssetSpec]:
    return [resolve_asset_spec_schema(context, asset) for asset in schema.assets]


class PipesSubprocessScriptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    path: str
    assets: Annotated[Sequence[AssetSpec], FieldResolver(resolve_assets)]


class PipesSubprocessScriptSchema(ResolvableSchema[PipesSubprocessScriptSpec]):
    path: str
    assets: Sequence[AssetSpecSchema]


class PipesSubprocessScriptCollectionSchema(
    ResolvableSchema["PipesSubprocessScriptCollectionComponent"]
):
    scripts: Sequence[PipesSubprocessScriptSchema]


def resolve_specs_by_path(
    context: ResolutionContext, schema: PipesSubprocessScriptCollectionSchema
) -> Mapping[str, Sequence[AssetSpec]]:
    return {spec.path: spec.assets for spec in context.resolve_value(schema.scripts)}


@dataclass
class PipesSubprocessScriptCollectionComponent(Component):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    # A mapping from Python script paths to the assets that are produced by the script
    specs_by_path: Annotated[
        Mapping[str, Sequence[AssetSpec]], FieldResolver(resolve_specs_by_path)
    ] = ...

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollectionComponent":
        path_specs = {str(path): [AssetSpec(path.stem)] for path in list(path.rglob("*.py"))}
        return PipesSubprocessScriptCollectionComponent(specs_by_path=path_specs)

    @classmethod
    def get_schema(cls) -> type[PipesSubprocessScriptCollectionSchema]:
        return PipesSubprocessScriptCollectionSchema

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
