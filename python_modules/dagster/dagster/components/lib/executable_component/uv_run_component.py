import shutil
from collections.abc import Iterable
from functools import cached_property

from dagster_shared import check

from dagster._core.definitions.assets.definition.computation import ComputationFn, ComputationResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent, OpSpec
from dagster.components.lib.executable_component.script_utils import (
    ScriptSpec,
    get_cmd,
    invoke_runner,
)


class UvRunComponent(ExecutableComponent):
    """Represents a Python script, alongside the set of assets or asset checks that it is responsible for executing.

    Accepts a path to a Python script which will be executed in a dagster-pipes subprocess using the `uv run` command.

    Example:
    ```yaml
    type: dagster.UvRunComponent
    attributes:
      execution:
        path: update_table.py
      assets:
        - key: my_table
    ```
    """

    execution: ScriptSpec

    @property
    def op_spec(self) -> OpSpec:
        return self._script_spec

    @cached_property
    def _script_spec(self) -> ScriptSpec:
        return ScriptSpec.with_script_stem_as_default_name(self.execution)

    def get_execute_fn(
        self,
        component_load_context: ComponentLoadContext,
    ) -> ComputationFn:
        check.invariant(not self.resource_keys, "Pipes subprocess scripts cannot have resources")

        def _fn(context: AssetExecutionContext) -> Iterable[ComputationResult]:
            command = get_cmd(
                script_runner_exe=[check.not_none(shutil.which("uv"), "uv not found"), "run"],
                spec=self.execution,
                path=str(component_load_context.path),
            )
            yield from invoke_runner(context=context, command=command)

        return _fn
