import shutil
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Union

from dagster_shared import check

from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent, OpSpec
from dagster.components.lib.executable_component.script_utils import (
    ScriptSpec,
    get_cmd,
    invoke_runner,
)

if TYPE_CHECKING:
    from dagster._core.execution.context.asset_check_execution_context import (
        AssetCheckExecutionContext,
    )
    from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
    from dagster._core.pipes.context import PipesExecutionResult


class UvRunComponent(ExecutableComponent):
    """Represents a Python script, alongside the set of assets or asset checks that it is responsible for executing.

    Accepts a path to a Python script which will be executed in a dagster-pipes subprocess using the `uv run` command.

    Example:
        .. code-block:: yaml

            type: dagster.UvRunComponent
            attributes:
              execution:
                path: update_table.py
              assets:
                - key: my_table
    """

    execution: ScriptSpec

    @property
    def op_spec(self) -> OpSpec:
        return self._script_spec

    @cached_property
    def _script_spec(self) -> ScriptSpec:
        return ScriptSpec.with_script_stem_as_default_name(self.execution)

    def invoke_execute_fn(
        self,
        context: Union["AssetExecutionContext", "AssetCheckExecutionContext"],
        component_load_context: ComponentLoadContext,
    ) -> Sequence["PipesExecutionResult"]:
        assert not self.resource_keys, "Pipes subprocess scripts cannot have resources"
        command = get_cmd(
            script_runner_exe=[check.not_none(shutil.which("uv"), "uv not found"), "run"],
            spec=self.execution,
            path=str(component_load_context.path),
        )
        return invoke_runner(context=context, command=command)
