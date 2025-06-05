import importlib
from collections.abc import Iterable
from functools import cached_property
from typing import Annotated, Callable, Literal, Union

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)
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


class FunctionSpec(OpMetadataSpec):
    type: Literal["function"] = "function"
    fn: ResolvableCallable


class ExecuteFnMetadata:
    def __init__(self, execute_fn: Callable):
        self.execute_fn = execute_fn
        found_args = {"context"} | self.resource_keys
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


class FunctionComponent(ExecutableComponent):
    ## Begin overloads
    execution: Union[FunctionSpec, ResolvableCallable]

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return (
            self.execution
            if isinstance(self.execution, FunctionSpec)
            else FunctionSpec(name=self.execution.__name__, fn=self.execution)
        )

    @property
    def resource_keys(self) -> set[str]:
        return self.execute_fn_metadata.resource_keys

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Iterable[Union[MaterializeResult, AssetCheckResult]]:
        rd = context.resources.original_resource_dict
        fn_kwargs = {k: v for k, v in rd.items() if k in self.resource_keys}
        check.invariant(set(fn_kwargs.keys()) == self.resource_keys, "Resource keys mismatch")
        return self.execute_fn_metadata.execute_fn(context, **fn_kwargs)

    ## End overloads

    @cached_property
    def execute_fn_metadata(self) -> "ExecuteFnMetadata":
        return ExecuteFnMetadata(check.inst(self.op_metadata_spec, FunctionSpec).fn)
