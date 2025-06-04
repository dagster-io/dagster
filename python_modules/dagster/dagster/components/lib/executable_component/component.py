import importlib
import inspect
from functools import cached_property
from typing import Annotated, Any, Callable, Optional, Union

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_check_decorator import multi_asset_check
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import ResolvedAssetCheckSpec, ResolvedAssetSpec
from dagster.components.resolved.model import Model, Resolver


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


def get_resources_from_callable(func: Callable) -> list[str]:
    sig = inspect.signature(func)
    return [param.name for param in sig.parameters.values() if param.name != "context"]


class ExecutableComponent(Component, Resolvable, Model):
    """Executable Component represents an executable node in the asset graph.

    It is comprised of an execute_fn, which is can be specified as a fully
    resolved symbol reference in yaml. This makes it a plain ole' Python function
    that does the execution within the asset graph.

    You can pass an arbitrary number of assets or asset checks to the component.

    With this structure this component replaces @asset, @multi_asset, @asset_check, and @multi_asset_check.
    which can all be expressed as a single ExecutableComponent.
    """

    # inferred from the function name if not provided
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    assets: Optional[list[ResolvedAssetSpec]] = None
    checks: Optional[list[ResolvedAssetCheckSpec]] = None
    execute_fn: ResolvableCallable

    @cached_property
    def execute_fn_metadata(self) -> "ExecuteFnMetadata":
        return ExecuteFnMetadata(self.execute_fn)

    @cached_property
    def resource_keys(self) -> set[str]:
        return self.execute_fn_metadata.resource_keys

    def build_underlying_assets_def(self) -> AssetsDefinition:
        if self.assets:

            @multi_asset(
                name=self.name or self.execute_fn.__name__,
                op_tags=self.tags,
                description=self.description,
                specs=self.assets,
                check_specs=self.checks,
                required_resource_keys=self.resource_keys,
            )
            def _assets_def(context: AssetExecutionContext, **kwargs):
                return self.invoke_execute_fn(context)

            return _assets_def
        elif self.checks:

            @multi_asset_check(
                name=self.name or self.execute_fn.__name__,
                op_tags=self.tags,
                specs=self.checks,
                description=self.description,
                required_resource_keys=self.resource_keys,
            )
            def _asset_check_def(context: AssetCheckExecutionContext, **kwargs):
                return self.invoke_execute_fn(context)

            return _asset_check_def

        check.failed("No assets or checks provided")

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets_def = self.build_underlying_assets_def()
        if isinstance(assets_def, AssetChecksDefinition):
            return Definitions(asset_checks=[assets_def])
        else:
            return Definitions(assets=[assets_def])

    def invoke_execute_fn(
        self, context: Union[AssetExecutionContext, AssetCheckExecutionContext]
    ) -> Any:
        rd = context.resources.original_resource_dict
        to_pass = {k: v for k, v in rd.items() if k in self.resource_keys}
        check.invariant(set(to_pass.keys()) == self.resource_keys, "Resource keys mismatch")
        return self.execute_fn(context, **to_pass)


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
