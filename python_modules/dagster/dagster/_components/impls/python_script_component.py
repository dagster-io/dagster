import shutil
from pathlib import Path
from typing import Optional, Sequence, Union

from dagster._components import Component, ComponentLoadContext
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient


class PythonScript(Component):
    path: Path
    specs: Sequence[AssetSpec]

    def __init__(self, path: Union[str, Path], specs: Optional[Sequence[AssetSpec]] = None):
        self.path = Path(path)
        self.specs = specs or [AssetSpec(key=self.path.stem)]

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        @multi_asset(specs=self.specs, name=f"script_{self.path.stem}")
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), self.path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return Definitions(assets=[_asset], resources=load_context.resources)
