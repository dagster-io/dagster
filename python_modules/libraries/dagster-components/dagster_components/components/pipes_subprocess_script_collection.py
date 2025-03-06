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

from dagster_components.core.component import Component, ComponentLoadContext
from dagster_components.core.schema.objects import AssetSpecModel, AssetSpecSequenceField
from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.model import FieldResolver, ResolvableModel, ResolvedFrom

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class PipesSubprocessScriptModel(ResolvableModel):
    path: str
    assets: Sequence[AssetSpecModel]


@dataclass
class PipesSubprocessScript(ResolvedFrom[PipesSubprocessScriptModel]):
    path: str
    assets: AssetSpecSequenceField


class PipesSubprocessScriptCollectionModel(ResolvableModel):
    scripts: Sequence[PipesSubprocessScriptModel]


@dataclass
class PipesSubprocessScriptCollectionComponent(
    Component, ResolvedFrom[PipesSubprocessScriptCollectionModel]
):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    # "A mapping from Python script paths to the assets that are produced by the script.",
    @staticmethod
    def resolve_specs_by_path(
        context: ResolutionContext, model: PipesSubprocessScriptCollectionModel
    ) -> Mapping[str, Sequence[AssetSpec]]:
        return {
            spec.path: spec.assets
            for spec in PipesSubprocessScript.from_seq(context, model.scripts)
        }

    specs_by_path: Annotated[
        Mapping[str, Sequence[AssetSpec]], FieldResolver.from_model(resolve_specs_by_path)
    ] = ...

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollectionComponent":
        path_specs = {str(path): [AssetSpec(path.stem)] for path in list(path.rglob("*.py"))}
        return PipesSubprocessScriptCollectionComponent(specs_by_path=path_specs)

    @classmethod
    def get_schema(cls) -> type[PipesSubprocessScriptCollectionModel]:
        return PipesSubprocessScriptCollectionModel

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
