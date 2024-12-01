import shutil
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

from pydantic import BaseModel, TypeAdapter

from dagster._components import Component, ComponentInitContext, ComponentLoadContext
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._utils.warnings import ExperimentalWarning

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            return AssetSpec(
                **{
                    **self.__dict__,
                    "key": AssetKey.from_user_string(self.key),
                },
            )


class PipesSubprocessScriptParams(BaseModel):
    assets: Sequence[AssetSpecModel]


class PipesSubprocessScriptCollection(Component):
    params_schema = Mapping[str, PipesSubprocessScriptParams]

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
    ) -> "PipesSubprocessScriptCollection":
        loaded_params = TypeAdapter(cls.params_schema).validate_python(component_params)
        return cls(
            dirpath=init_context.path,
            path_specs={
                k: [vv.to_asset_spec() for vv in v.assets] for k, v in loaded_params.items()
            }
            if loaded_params
            else None,
        )

    def build_defs(self, load_context: "ComponentLoadContext") -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions(
            assets=[self._create_asset_def(path) for path in list(self.dirpath.rglob("*.py"))],
            resources={"pipes_client": PipesSubprocessClient()},
        )

    def _create_asset_def(self, path: Path):
        @multi_asset(
            specs=self.path_specs.get(path.stem) or [AssetSpec(key=path.stem)],
            name=f"script_{path.stem}",
        )
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return _asset
