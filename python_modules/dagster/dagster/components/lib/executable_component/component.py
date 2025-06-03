import importlib
import inspect
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import Annotated, Any, Callable, Optional, Union, get_args, get_origin

from dagster_shared import check
from dagster_shared.record import record
from typing_extensions import TypeAlias

from dagster._core.decorator_utils import get_function_params, get_type_hints
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.asset_check_decorator import multi_asset_check
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import Output
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.execution.plan.outputs import StepOutputData
from dagster._core.types.dagster_type import Any as DagsterAny
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

    @cached_property
    def asset_outs(self) -> Mapping[str, AssetOut]:
        return specs_to_asset_outs(self.assets or [])

    def name_for_asset_key(self, asset_key: Optional[AssetKey]) -> str:
        if asset_key is None:
            return next(iter(self.asset_outs.keys()))
        for name, asset_out in self.asset_outs.items():
            if asset_out.key == asset_key:
                return name
        raise Exception(f"Asset key {asset_key} not found in {self.asset_outs}")

    @cached_property
    def implicit_asset_key(self) -> AssetKey:
        assets = self.assets or []
        check.invariant(
            len(assets) == 1, "Implicit asset key is only supported for single asset components"
        )
        return assets[0].key

    @cached_property
    def underlying_assets_def(self) -> AssetsDefinition:
        if self.assets:

            @multi_asset(
                name=self.name or self.execute_fn.__name__,
                op_tags=self.tags,
                description=self.description,
                check_specs=self.checks,
                ins=specs_to_asset_ins(self.assets),
                outs=self.asset_outs,
                required_resource_keys=self.resource_keys,
            )
            def _assets_def(context: AssetExecutionContext, **kwargs):
                return self.invoke_execute_fn(context, kwargs)

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
                return self.invoke_execute_fn(context, kwargs)

            return _asset_check_def

        check.failed("No assets or checks provided")

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        for asset in self.assets or []:
            for comp in asset.key.path:
                if "/" in comp:
                    raise Exception(f"Asset key {asset.key} contains a '/'")

        assets_def = self.underlying_assets_def
        if isinstance(assets_def, AssetChecksDefinition):
            return Definitions(asset_checks=[assets_def])
        else:
            return Definitions(assets=[assets_def])

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        input_objects_by_input_name: Mapping[str, Any],
    ) -> Any:
        rd = context.resources.original_resource_dict
        resource_args = {k: v for k, v in rd.items() if k in self.resource_keys}
        check.invariant(set(resource_args.keys()) == self.resource_keys, "Resource keys mismatch")

        # remap input names to local fn param names
        local_inputs = self.remap_to_local_inputs(input_objects_by_input_name)

        result = self.execute_fn(context, **{**resource_args, **local_inputs})

        for item in self.canonicalize_to_iterator(result):
            if isinstance(item, MaterializeResult):
                value = {**(result.metadata or {})}.pop(VALUE_METADATA_KEY, None)
                yield embellish_output(
                    Output(
                        output_name=self.name_for_asset_key(item.asset_key),
                        value=value,
                        metadata=item.metadata,
                        tags=item.tags,
                        data_version=item.data_version,
                    ),
                    asset_key=item.asset_key or self.implicit_asset_key,
                )
                if item.check_results:
                    yield from item.check_results
            elif isinstance(item, AssetCheckResult):
                yield item
            else:
                check.failed(f"Unexpected result type: {type(result)}")

    def canonicalize_to_iterator(self, result):
        if isinstance(result, MaterializeResult):
            return [result]
        elif isinstance(result, AssetCheckResult):
            return [result]
        else:
            return result

    def remap_to_local_inputs(self, input_objects_by_input_name):
        local_inputs = {}
        for input_name, input_object in input_objects_by_input_name.items():
            for upstream_param_info in self.execute_fn_metadata.upstream_args.values():
                if input_name == upstream_param_info.asset_key.to_python_identifier():
                    local_inputs[upstream_param_info.param_name] = input_object
        return local_inputs


def specs_to_asset_ins(specs: Sequence[AssetSpec]) -> Mapping[str, AssetIn]:
    ins: dict[str, AssetIn] = {}
    for spec in specs:
        for dep in spec.deps:
            ins[dep.asset_key.to_python_identifier()] = AssetIn(
                key=dep.asset_key,
                dagster_type=DagsterAny,
            )

    return ins


def specs_to_asset_outs(specs: Sequence[AssetSpec]) -> Mapping[str, AssetOut]:
    outs: dict[str, AssetOut] = {}
    for spec in specs:
        outs[spec.key.to_python_identifier()] = AssetOut(
            key=spec.key,
            description=spec.description,
            tags=spec.tags,
            metadata=spec.metadata,
            dagster_type=DagsterAny,
        )

    return outs


class ExecuteFnMetadata:
    def __init__(self, execute_fn: Callable):
        self.execute_fn = execute_fn
        found_args = {"context"} | self.resource_keys | set(self.upstream_args.keys())
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
    def upstream_args(self) -> dict[str, "UpstreamParamInfo"]:
        return get_upstream_args(self.execute_fn)

    @cached_property
    def upstreams_by_asset_key(self) -> Mapping[AssetKey, "UpstreamParamInfo"]:
        return {
            upstream.asset_key: upstream
            for upstream in self.upstream_args.values()
            if upstream.asset_key
        }


@record
class Upstream:
    asset_key: Optional[CoercibleToAssetKey] = None


@record(checked=False)  # doesn't handle type
class UpstreamParamInfo:
    param_name: str
    type: type
    asset_key: AssetKey


def get_upstream_args(func: Callable) -> dict[str, UpstreamParamInfo]:
    """Get all parameters annotated with UpstreamParam.

    Args:
        func: The function to inspect

    Returns:
        A dictionary mapping parameter names to tuples of (type, UpstreamParam instance)
    """
    result = {}
    type_annotations = get_type_hints(func)
    for param in get_function_params(func):
        if param.name not in type_annotations:
            continue

        if get_origin(param.annotation) is not Annotated:
            continue

        type_args = get_args(param.annotation)
        if len(type_args) != 2 or not isinstance(type_args[1], Upstream):
            continue

        upstream = check.inst(type_args[1], Upstream)
        asset_key = (
            AssetKey.from_coercible(upstream.asset_key)
            if upstream.asset_key
            else AssetKey(param.name)
        )
        result[param.name] = UpstreamParamInfo(
            param_name=param.name, type=type_args[0], asset_key=asset_key
        )

    return result


VALUE_METADATA_KEY = "dagster/value"


def materialize_result_with_value(
    *,
    asset_key: Optional[CoercibleToAssetKey] = None,
    value: Any = None,
    metadata: Optional[RawMetadataMapping] = None,
    check_results: Optional[Sequence[AssetCheckResult]] = None,
    data_version: Optional[DataVersion] = None,
    tags: Optional[dict[str, str]] = None,
) -> MaterializeResult:
    return MaterializeResult(
        asset_key=asset_key,
        metadata={**(metadata or {}), VALUE_METADATA_KEY: value},
        check_results=check_results,
        data_version=data_version,
        tags=tags,
    )


ASSET_KEY_METADATA_KEY = "dagster/asset_key"


def embellish_output(output: Output, asset_key: AssetKey) -> Output:
    return output.with_metadata(
        {**(output.metadata or {}), ASSET_KEY_METADATA_KEY: asset_key.to_user_string()}
    )


def value_for_asset(result: ExecuteInProcessResult, asset_key: CoercibleToAssetKey) -> Any:
    asset_key = AssetKey.from_coercible(asset_key)
    for event in result.all_events:
        if isinstance(event.event_specific_data, StepOutputData):
            metadata_entry = event.event_specific_data.metadata.get(ASSET_KEY_METADATA_KEY, None)
            if (
                isinstance(metadata_entry, TextMetadataValue)
                and metadata_entry.value == asset_key.to_user_string()
            ):
                step_output_handle = event.event_specific_data.step_output_handle
                return result.output_for_node(
                    step_output_handle.step_key, step_output_handle.output_name
                )
    return None
