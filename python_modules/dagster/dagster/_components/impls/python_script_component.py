import shutil
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from pydantic import BaseModel, TypeAdapter

from dagster._components import ComponentInitContext, ComponentLoadContext, FileCollectionComponent
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient


class AssetSpecModel(BaseModel):
    key: str
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Mapping[str, Any] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Mapping[str, str] = {}

    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            **{
                **self.__dict__,
                "key": AssetKey.from_user_string(self.key),
            },
        )


class PythonScriptParams(BaseModel):
    assets: Sequence[AssetSpecModel]


class PythonScriptCollection(FileCollectionComponent):
    params_schema = Mapping[str, PythonScriptParams]

    def __init__(
        self, dirpath: Path, path_specs: Optional[Mapping[str, Sequence[AssetSpec]]] = None
    ):
        self.dirpath = dirpath
        # mapping from the script name (e.g. /path/to/script_abc.py -> script_abc)
        # to the specs it produces
        self.path_specs = path_specs or {}

    @classmethod
    def from_component_params(
        cls, init_context: ComponentInitContext, component_params: object
    ) -> "PythonScriptCollection":
        loaded_params = TypeAdapter(cls.params_schema).validate_python(component_params)
        return cls(
            dirpath=init_context.path,
            path_specs={
                k: [vv.to_asset_spec() for vv in v.assets] for k, v in loaded_params.items()
            }
            if loaded_params
            else None,
        )

    def loadable_paths(self) -> Sequence[Path]:
        return list(self.dirpath.rglob("*.py"))

    def build_defs_for_path(self, path: Path, load_context: ComponentLoadContext) -> Definitions:
        @multi_asset(
            specs=self.path_specs.get(path.stem) or [AssetSpec(key=path.stem)],
            name=f"script_{path.stem}",
        )
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return Definitions(assets=[_asset], resources=load_context.resources)
