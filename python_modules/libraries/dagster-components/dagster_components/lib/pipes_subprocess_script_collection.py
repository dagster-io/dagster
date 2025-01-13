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

from dagster_components.core.component import Component, ComponentLoadContext, component_type
from dagster_components.core.schema.objects import AssetAttributesModel

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class PipesSubprocessScriptParams(BaseModel):
    path: str
    assets: Sequence[AssetAttributesModel]


class PipesSubprocessScriptCollectionParams(BaseModel):
    scripts: Sequence[PipesSubprocessScriptParams]


@component_type(name="pipes_subprocess_script_collection")
class PipesSubprocessScriptCollection(Component):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    def __init__(self, dirpath: Path, path_specs: Mapping[Path, Sequence[AssetSpec]]):
        self.dirpath = dirpath
        # mapping from the script name (e.g. /path/to/script_abc.py -> script_abc)
        # to the specs it produces
        self.path_specs = path_specs

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollection":
        path_specs = {path: [AssetSpec(path.stem)] for path in list(path.rglob("*.py"))}
        return PipesSubprocessScriptCollection(dirpath=path, path_specs=path_specs)

    @classmethod
    def get_schema(cls):
        return PipesSubprocessScriptCollectionParams

    @classmethod
    def load(cls, context: ComponentLoadContext) -> "PipesSubprocessScriptCollection":
        loaded_params = context.load_params(cls.get_schema())

        path_specs = {}
        for script in loaded_params.scripts:
            script_path = context.path / script.path
            if not script_path.exists():
                raise FileNotFoundError(f"Script {script_path} does not exist")
            path_specs[script_path] = [
                AssetSpec(**asset.resolve_properties(context.templated_value_resolver))
                for asset in script.assets
            ]

        return cls(dirpath=context.path, path_specs=path_specs)

    def build_defs(self, context: "ComponentLoadContext") -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions(
            assets=[self._create_asset_def(path, specs) for path, specs in self.path_specs.items()],
            resources={"pipes_client": PipesSubprocessClient()},
        )

    def _create_asset_def(self, path: Path, specs: Sequence[AssetSpec]) -> AssetsDefinition:
        # TODO: allow name paraeterization
        @multi_asset(specs=specs, name=f"script_{path.stem}")
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return _asset
