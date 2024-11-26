import shutil
from pathlib import Path
from typing import Any, ClassVar, Mapping, Optional, Sequence, Type, Union

from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster._components import ComponentInitContext, ComponentLoadContext, LoadableComponent
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


class PythonScript(LoadableComponent):
    params_schema: ClassVar[Type[Optional[Sequence[AssetSpecModel]]]] = Optional[
        Sequence[AssetSpecModel]
    ]
    path: Path
    specs: Sequence[AssetSpec]

    def __init__(self, path: Union[str, Path], specs: Optional[Sequence[AssetSpec]] = None):
        self.path = Path(path)
        self.specs = specs or [AssetSpec(key=self.path.stem)]

    @classmethod
    def from_component_params(
        cls, path: Path, component_params: object, context: ComponentInitContext
    ) -> Self:
        models = TypeAdapter(cls.params_schema).validate_python(component_params)
        specs = [s.to_asset_spec() for s in models] if models else None
        return cls(path=path, specs=specs)

    @classmethod
    def loadable_paths(cls, path: Path) -> Sequence[Path]:
        return list(path.rglob("*.py"))

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        @multi_asset(specs=self.specs, name=f"script_{self.path.stem}")
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), self.path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return Definitions(assets=[_asset], resources=load_context.resources)
