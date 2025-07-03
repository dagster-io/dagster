import inspect
from collections.abc import AsyncIterator, Awaitable, Iterator, Mapping, Sequence
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

from typing_extensions import get_args

from dagster._config.pythonic_config import Config
from dagster._core.definitions import (
    AssetCheckResult,
    AssetMaterialization,
    DynamicOutput,
    ExpectationResult,
    Output,
    OutputDefinition,
)
from dagster._core.definitions.input import InputDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.result import AssetResult, ObserveResult
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.compute import ExecutionContextTypes
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.types.dagster_type import DagsterTypeKind, is_generic_output_annotation
from dagster._utils import is_named_tuple_instance
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction


def create_op_compute_wrapper(
    op_def: OpDefinition,
) -> Callable[[ExecutionContextTypes, Mapping[str, InputDefinition]], Any]:
    compute_fn = cast("DecoratedOpFunction", op_def.compute_fn)
    fn = compute_fn.decorated_fn
    input_defs = op_def.input_defs
    output_defs = op_def.output_defs
    context_arg_provided = compute_fn.has_context_arg()
    config_arg_cls = compute_fn.get_config_arg().annotation if compute_fn.has_config_arg() else None
    resource_arg_mapping = {arg.name: arg.name for arg in compute_fn.get_resource_args()}

    input_names = [
        input_def.name
        for input_def in input_defs
        if not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ]

    @wraps(fn)
    def compute(
        context: ExecutionContextTypes,
        input_defs: Mapping[str, InputDefinition],
    ) -> Union[Iterator[Output], AsyncIterator[Output]]:
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        if (
            inspect.isgeneratorfunction(fn)
            or inspect.isasyncgenfunction(fn)
            or inspect.iscoroutinefunction(fn)
        ):
            # safe to execute the function, as doing so will not immediately execute user code
            result = invoke_compute_fn(
                fn, context, kwargs, context_arg_provided, config_arg_cls, resource_arg_mapping
            )
            if inspect.iscoroutine(result):
                return _coerce_async_op_to_async_gen(result, context, output_defs)
            # already a generator
            return result
        else:
            # we have a regular function, do not execute it before we are in an iterator
            # (as we want all potential failures to happen inside iterators)
            return _coerce_op_compute_fn_to_iterator(
                fn,
                output_defs,
                context,
                context_arg_provided,
                kwargs,
                config_arg_cls,
                resource_arg_mapping,
            )

    return compute


async def _coerce_async_op_to_async_gen(
    awaitable: Awaitable[Any],
    context: ExecutionContextTypes,
    output_defs: Sequence[OutputDefinition],
) -> AsyncIterator[Any]:
    result = await awaitable
    for event in validate_and_coerce_op_result_to_iterator(result, context, output_defs):
        yield event


def invoke_compute_fn(
    fn: Callable[..., Any],
    context: ExecutionContextTypes,
    kwargs: Mapping[str, Any],
    context_arg_provided: bool,
    config_arg_cls: Optional[type[Config]],
    resource_args: Optional[dict[str, str]] = None,
) -> Any:
    args_to_pass = {**kwargs}
    if config_arg_cls:
        # config_arg_cls is either a Config class or a primitive type
        if issubclass(config_arg_cls, Config):
            args_to_pass["config"] = construct_config_from_context(
                config_arg_cls, context.op_execution_context
            )
        else:
            args_to_pass["config"] = context.op_execution_context.op_config
    if resource_args:
        for resource_name, arg_name in resource_args.items():
            args_to_pass[arg_name] = context.resources.original_resource_dict[resource_name]

    return fn(context, **args_to_pass) if context_arg_provided else fn(**args_to_pass)


def construct_config_from_context(
    config_arg_cls: type[Config], op_execution_context: OpExecutionContext
) -> Config:
    return config_arg_cls(
        **config_arg_cls._get_non_default_public_field_values_cls(op_execution_context.op_config)  # noqa: SLF001
    )


def _coerce_op_compute_fn_to_iterator(
    fn,
    output_defs,
    context: ExecutionContextTypes,
    context_arg_provided,
    kwargs,
    config_arg_class,
    resource_arg_mapping,
):
    result = invoke_compute_fn(
        fn, context, kwargs, context_arg_provided, config_arg_class, resource_arg_mapping
    )
    yield from validate_and_coerce_op_result_to_iterator(result, context, output_defs)


def _zip_and_iterate_op_result(
    result: Any, context: ExecutionContextTypes, output_defs: Sequence[OutputDefinition]
) -> Iterator[tuple[int, Any, OutputDefinition]]:
    # Filtering the expected output defs here is an unfortunate temporary solution to deal with the
    # change in expected outputs that occurs as a result of putting `AssetCheckResults` onto
    # `MaterializeResults`. Prior to this, `AssetCheckResults` were yielded/returned directly, and
    # thus were expected to always be included in the result tuple. Thus we need to remove them from
    # the expected output defs if they have been included indirectly via embedding in a
    # `MaterializeResult`.
    #
    # A better solution is surely possible here in a future refactor. The major complicating element
    # is the conversion of MaterializeResult into Output, which currently happens in
    # execute_step.py and leverages job_def.asset_layer. There is difficulty in moving that logic up
    # to here because we can't rely on the presence of asset layer here, since the present code path
    # is used by direct invocation. Probably the solution is to expose an asset layer on the
    # invocation context.
    expected_return_outputs = _filter_expected_output_defs(result, context, output_defs)
    if len(expected_return_outputs) > 1:
        result = _validate_multi_return(context, result, expected_return_outputs)
        for position, (output_def, element) in enumerate(zip(expected_return_outputs, result)):
            yield position, output_def, element
    else:
        yield 0, output_defs[0], result


# Filter out output_defs corresponding to asset check results that already exist on a
# MaterializeResult.
def _filter_expected_output_defs(
    result: Any, context: ExecutionContextTypes, output_defs: Sequence[OutputDefinition]
) -> Sequence[OutputDefinition]:
    result_tuple = (
        (result,) if not isinstance(result, tuple) or is_named_tuple_instance(result) else result
    )
    asset_results = [x for x in result_tuple if isinstance(x, AssetResult)]

    if not asset_results:
        return output_defs

    check_names_by_asset_key = {}
    for check_key in context.op_execution_context.selected_asset_check_keys:
        if check_key.asset_key not in check_names_by_asset_key:
            check_names_by_asset_key[check_key.asset_key] = []
        check_names_by_asset_key[check_key.asset_key].append(check_key.name)

    remove_outputs = []
    for asset_result in asset_results:
        for check_result in asset_result.check_results:
            remove_outputs.append(
                context.op_execution_context.assets_def.get_output_name_for_asset_check_key(
                    check_result.resolve_target_check_key(check_names_by_asset_key)
                )
            )

    return [out for out in output_defs if out.name not in remove_outputs]


def _validate_multi_return(
    context: ExecutionContextTypes,
    result: Any,
    output_defs: Sequence[OutputDefinition],
) -> Any:
    # special cases for implicit/explicit returned None
    if result is None:
        # extrapolate None -> (None, None, ...) when appropriate
        if all(
            output_def.dagster_type.is_nothing and output_def.is_required
            for output_def in output_defs
        ):
            return [None for _ in output_defs]

    # When returning from an op with multiple outputs, the returned object must be a tuple of the same length as the number of outputs. At the time of the op's construction, we verify that a provided annotation is a tuple with the same length as the number of outputs, so if the result matches the number of output defs on the op, it will transitively also match the annotation.
    if not isinstance(result, tuple):
        raise DagsterInvariantViolationError(
            f"{context.describe_op()} has multiple outputs, but only one "
            f"output was returned of type {type(result)}. When using "
            "multiple outputs, either yield each output, or return a tuple "
            "containing a value for each output. Check out the "
            "documentation on outputs for more: "
            "https://legacy-docs.dagster.io/concepts/ops-jobs-graphs/ops#outputs."
        )
    output_tuple = cast("tuple", result)
    if not len(output_tuple) == len(output_defs):
        raise DagsterInvariantViolationError(
            "Length mismatch between returned tuple of outputs and number of "
            f"output defs on {context.describe_op()}. Output tuple has "
            f"{len(output_tuple)} outputs, while "
            f"{context.op_def.node_type_str} has {len(output_defs)} outputs."
        )
    return result


def _get_annotation_for_output_position(
    position: int, op_def: OpDefinition, output_defs: Sequence[OutputDefinition]
) -> Any:
    if op_def.is_from_decorator():
        if len(output_defs) > 1:
            annotation_subitems = get_args(op_def.get_output_annotation())
            if len(annotation_subitems) == len(output_defs):
                return annotation_subitems[position]
        else:
            return op_def.get_output_annotation()

    return inspect.Parameter.empty


def _check_output_object_name(
    output: Union[DynamicOutput, Output], output_def: OutputDefinition, position: int
) -> None:
    from dagster._core.definitions.events import DEFAULT_OUTPUT

    if not output.output_name == DEFAULT_OUTPUT and not output.output_name == output_def.name:
        raise DagsterInvariantViolationError(
            f"Bad state: Output was explicitly named '{output.output_name}', "
            "which does not match the output definition specified for position "
            f"{position}: '{output_def.name}'."
        )


def validate_and_coerce_op_result_to_iterator(
    result: Any,
    context: ExecutionContextTypes,
    output_defs: Sequence[OutputDefinition],
) -> Iterator[Any]:
    if inspect.isgenerator(result):
        # this happens when a user explicitly returns a generator in the op
        yield from result
    elif isinstance(result, (AssetMaterialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: If you are "
            "returning an AssetMaterialization "
            "or an ExpectationResult from "
            f"{context.op_def.node_type_str} you must yield them "
            "directly, or log them using the context.log_event method to avoid "
            "ambiguity with an implied result from returning a "
            "value. Check out the docs on logging events here: "
            "https://legacy-docs.dagster.io/concepts/ops-jobs-graphs/op-events#op-events-and-exceptions"
        )
    # These don't correspond to output defs so pass them through
    elif isinstance(result, (AssetCheckResult, ObserveResult)):
        yield result
    elif result is not None and not output_defs:
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: Unexpectedly returned output of type"
            f" {type(result)}. {context.op_def.node_type_str.capitalize()} is explicitly defined to"
            " return no results."
        )
    # `requires_typed_event_stream` is a mode where we require users to return/yield exactly the
    # results that will be registered in the instance, without additional fancy inference (like
    # wrapping `None` in an `Output`). We therefore skip any return-specific validation for this
    # mode and treat returned values as if they were yielded.
    elif output_defs and context.op_execution_context.requires_typed_event_stream:
        # If nothing was returned, treat it as an empty tuple instead of a `(None,)`.
        # This is important for delivering the correct error message when an output is missing.
        if result is None:
            result_tuple = tuple()
        elif not isinstance(result, tuple) or is_named_tuple_instance(result):
            result_tuple = (result,)
        else:
            result_tuple = result
        yield from result_tuple
    elif output_defs:
        for position, output_def, element in _zip_and_iterate_op_result(
            result, context, output_defs
        ):
            annotation = _get_annotation_for_output_position(position, context.op_def, output_defs)
            if output_def.is_dynamic:
                if not isinstance(element, list):
                    raise DagsterInvariantViolationError(
                        f"Error with output for {context.describe_op()}: "
                        f"dynamic output '{output_def.name}' expected a list of "
                        "DynamicOutput objects, but instead received instead an "
                        f"object of type {type(element)}."
                    )
                for item in element:
                    if not isinstance(item, DynamicOutput):
                        raise DagsterInvariantViolationError(
                            f"Error with output for {context.describe_op()}: "
                            f"dynamic output '{output_def.name}' at position {position} expected a "
                            "list of DynamicOutput objects, but received an "
                            f"item with type {type(item)}."
                        )
                    dynamic_output = cast("DynamicOutput", item)
                    _check_output_object_name(dynamic_output, output_def, position)

                    with disable_dagster_warnings():
                        yield DynamicOutput(
                            output_name=output_def.name,
                            value=dynamic_output.value,
                            mapping_key=dynamic_output.mapping_key,
                            metadata=dynamic_output.metadata,
                        )
            elif isinstance(element, AssetResult):
                yield element  # coerced in to Output in outer iterator
            elif isinstance(element, Output):
                if annotation != inspect.Parameter.empty and not is_generic_output_annotation(
                    annotation
                ):
                    raise DagsterInvariantViolationError(
                        f"Error with output for {context.describe_op()}: received Output object for"
                        f" output '{output_def.name}' which does not have an Output annotation."
                        f" Annotation has type {annotation}."
                    )
                _check_output_object_name(element, output_def, position)

                with disable_dagster_warnings():
                    output = Output(
                        output_name=output_def.name,
                        value=element.value,
                        metadata=element.metadata,
                        data_version=element.data_version,
                        tags=element.tags,
                    )

                yield output

            else:
                # If annotation indicates a generic output annotation, and an
                # output object was not received, throw an error.
                if is_generic_output_annotation(annotation):
                    raise DagsterInvariantViolationError(
                        f"Error with output for {context.describe_op()}: output "
                        f"'{output_def.name}' has generic output annotation, "
                        "but did not receive an Output object for this output. "
                        f"Received instead an object of type {type(element)}."
                    )
                if result is None and output_def.is_required is False:
                    context.log.warning(
                        'Value "None" returned for non-required output '
                        f'"{output_def.name}" of {context.describe_op()}. '
                        "This value will be passed to downstream "
                        f"{context.op_def.node_type_str}s. For conditional "
                        "execution, results must be yielded: "
                        "https://legacy-docs.dagster.io/concepts/ops-jobs-graphs/graphs#with-conditional-branching"
                    )
                yield Output(output_name=output_def.name, value=element)
