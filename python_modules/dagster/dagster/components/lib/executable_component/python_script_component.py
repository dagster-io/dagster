import shutil
from collections.abc import Sequence
from functools import cached_property
from typing import Union

from dagster_shared import check

from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)
from dagster.components.lib.executable_component.script_utils import (
    ScriptSpec,
    get_cmd,
    invoke_runner,
)


class PythonScriptComponent(ExecutableComponent):
    execution: ScriptSpec

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return self._subprocess_spec

    @cached_property
    def _subprocess_spec(self) -> ScriptSpec:
        return ScriptSpec.with_script_stem_as_default_name(self.execution)

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Sequence[PipesExecutionResult]:
        assert not self.resource_keys, "Pipes subprocess scripts cannot have resources"
        return invoke_runner(
            context=context,
            command=get_cmd(
                script_runner_exe=[check.not_none(shutil.which("python"), "python not found")],
                spec=self.execution,
                path=str(component_load_context.path),
            ),
        )
