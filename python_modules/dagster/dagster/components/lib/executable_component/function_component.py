import importlib
from typing import Annotated, Callable, Literal, Union

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._core.definitions.assets.definition.computation import ComputationFn
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent, OpSpec
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.model import Resolver


def resolve_callable(context: ResolutionContext, model: str) -> Callable:
    load_context = ComponentLoadContext.from_resolution_context(context)
    if model.startswith("."):
        local_module_path, fn_name = model.rsplit(".", 1)
        module_path = f"{load_context.defs_module_name}.{local_module_path[1:]}"
    else:
        module_path, fn_name = model.rsplit(".", 1)

    module = importlib.import_module(module_path)
    return getattr(module, fn_name)


ResolvableCallable: TypeAlias = Annotated[
    Callable, Resolver(resolve_callable, model_field_type=str)
]


class FunctionSpec(OpSpec):
    type: Literal["function"] = "function"
    fn: ResolvableCallable


class FunctionComponent(ExecutableComponent):
    """Represents a Python function, alongside the set of assets or asset checks that it is responsible for executing.

    The provided function should return either a `MaterializeResult` or an `AssetCheckResult`.

    Examples:
    ```yaml
    type: dagster.FunctionComponent
    attributes:
      execution:
        fn: .my_module.update_table
      assets:
        - key: my_table
    ```

    ```python
    from dagster import MaterializeResult

    def update_table(context: AssetExecutionContext) -> MaterializeResult:
        # ...
        return MaterializeResult(metadata={"rows_updated": 100})

    @component
    def my_component():
        return FunctionComponent(
            execution=update_table,
            assets=[AssetSpec(key="my_table")],
        )
    ```

    """

    ## Begin overloads
    execution: Union[FunctionSpec, ResolvableCallable]

    @property
    def op_spec(self) -> OpSpec:
        return (
            self.execution
            if isinstance(self.execution, FunctionSpec)
            else FunctionSpec(name=self.execution.__name__, fn=self.execution)
        )

    def get_execute_fn(self, component_load_context: ComponentLoadContext) -> ComputationFn:
        return check.inst(self.op_spec, FunctionSpec).fn
