import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from pydantic import BaseModel

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    registered_component_type,
)
from dagster_components.core.schema.base import ResolvableModel
from dagster_components.core.schema.objects import AssetSpecModel
from dagster_components.core.schema.resolver import TemplatedValueResolver

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class PipesSubprocessScriptParams(BaseModel):
    path: str
    assets: Sequence[AssetSpecModel]


class PipesSubprocessScriptCollectionParams(ResolvableModel[Mapping[Path, Sequence[AssetSpec]]]):
    scripts: Sequence[PipesSubprocessScriptParams]

    def resolve(self, resolver: TemplatedValueResolver) -> Mapping[str, Sequence[AssetSpec]]:
        return {
            resolver.resolve_obj(script.path): [
                asset_model.resolve(resolver) for asset_model in script.assets
            ]
            for script in self.scripts
        }


@registered_component_type(name="pipes_subprocess_script_collection")
class PipesSubprocessScriptCollection(Component):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    def __init__(self, dirpath: Path, specs_by_path: Mapping[str, Sequence[AssetSpec]]):
        self.dirpath = dirpath
        # mapping from the script name (e.g. /path/to/script_abc.py -> script_abc)
        # to the specs it produces
        self.specs_by_path = specs_by_path

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollection":
        path_specs = {str(path): [AssetSpec(path.stem)] for path in list(path.rglob("*.py"))}
        return PipesSubprocessScriptCollection(dirpath=path, specs_by_path=path_specs)

    @classmethod
    def get_schema(cls) -> type[PipesSubprocessScriptCollectionParams]:
        return PipesSubprocessScriptCollectionParams

    @classmethod
    def load(
        cls, params: PipesSubprocessScriptCollectionParams, context: ComponentLoadContext
    ) -> "PipesSubprocessScriptCollection":
        return cls(
            dirpath=context.path, specs_by_path=params.resolve(context.templated_value_resolver)
        )

    def build_defs(self, context: "ComponentLoadContext") -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions(
            assets=[
                self._create_asset_def(self.dirpath / path, specs)
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
