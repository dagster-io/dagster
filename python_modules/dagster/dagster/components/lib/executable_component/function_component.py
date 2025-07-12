import importlib
from collections.abc import Iterable
from functools import cached_property
from typing import Annotated, Any, Callable, Literal, Optional, Union

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._config.field import Field
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.inference import get_config_param_type
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.plan.compute_generator import construct_config_from_context
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


class ExecuteFnMetadata:
    def __init__(self, execute_fn: Callable):
        self.execute_fn = execute_fn
        found_args = {"context"} | self.resource_keys | ({"config"} if self.config_cls else set())
        extra_args = self.function_params_names - found_args
        if extra_args:
            check.failed(
                f"Found extra arguments in execute_fn: {extra_args}. "
                "Arguments must be valid resource params or annotated with Upstream"
            )

    @cached_property
    def resource_keys(self) -> set[str]:
        return {arg.name for arg in get_resource_args(self.execute_fn)}

    @cached_property
    def function_params_names(self) -> set[str]:
        return {arg.name for arg in get_function_params(self.execute_fn)}

    @cached_property
    def config_cls(self) -> Union[type, None]:
        return get_config_param_type(self.execute_fn)

    @cached_property
    def config_fields(self) -> Optional[dict[str, Field]]:
        return self.config_cls.to_fields_dict() if self.config_cls else None


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

    @property
    def resource_keys(self) -> set[str]:
        return self.execute_fn_metadata.resource_keys

    @cached_property
    def config_fields(self) -> Optional[dict[str, Field]]:
        return self.execute_fn_metadata.config_fields

    @property
    def config_cls(self) -> Optional[type]:
        return self.execute_fn_metadata.config_cls

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Iterable[Union[MaterializeResult, AssetCheckResult]]:
        rd = context.resources.original_resource_dict
        expected_fn_kwargs = self.resource_keys | ({"config"} if self.config_cls else set())

        fn_kwargs = {
            **{k: v for k, v in rd.items() if k in self.resource_keys},
            **self.get_config_param_dict(context),
        }

        check.invariant(
            set(fn_kwargs.keys()) == expected_fn_kwargs, "Expected function param mismatch"
        )
        return self.execute_fn_metadata.execute_fn(context, **fn_kwargs)

    def get_config_param_dict(
        self, context: Union[AssetExecutionContext, AssetCheckExecutionContext]
    ) -> dict[str, Any]:
        if not self.config_cls:
            return {}
        return {
            "config": construct_config_from_context(self.config_cls, context.op_execution_context)
        }

    ## End overloads

    @cached_property
    def execute_fn_metadata(self) -> "ExecuteFnMetadata":
        return ExecuteFnMetadata(check.inst(self.op_spec, FunctionSpec).fn)
