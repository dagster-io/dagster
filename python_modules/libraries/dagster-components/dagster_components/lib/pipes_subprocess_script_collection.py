import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._utils.warnings import suppress_dagster_warnings
from pydantic import BaseModel

from dagster_components.core.component import Component, ComponentLoadContext, component
from dagster_components.core.dsl_schema import AutomationConditionModel

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
    automation_condition: Optional[AutomationConditionModel] = None

    @suppress_dagster_warnings
    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            **{
                **self.__dict__,
                "key": AssetKey.from_user_string(self.key),
                "automation_condition": self.automation_condition.to_automation_condition()
                if self.automation_condition
                else None,
            },
        )


class PipesSubprocessScriptParams(BaseModel):
    path: str
    assets: Sequence[AssetSpecModel]


class PipesSubprocessScriptCollectionParams(BaseModel):
    scripts: Sequence[PipesSubprocessScriptParams]


@component(name="pipes_subprocess_script_collection")
class PipesSubprocessScriptCollection(Component):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    params_schema = PipesSubprocessScriptCollectionParams

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
    def load(cls, context: ComponentLoadContext) -> "PipesSubprocessScriptCollection":
        loaded_params = context.load_params(cls.params_schema)

        path_specs = {}
        for script in loaded_params.scripts:
            script_path = context.path / script.path
            if not script_path.exists():
                raise FileNotFoundError(f"Script {script_path} does not exist")
            path_specs[script_path] = [spec.to_asset_spec() for spec in script.assets]

        return cls(dirpath=context.path, path_specs=path_specs)

    def build_defs(self, load_context: "ComponentLoadContext") -> "Definitions":
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
