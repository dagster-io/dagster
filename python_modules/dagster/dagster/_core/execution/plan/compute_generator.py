import inspect
import warnings
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import get_args

from dagster._config.structured_config import Config
from dagster._core.definitions import (
    AssetMaterialization,
    DynamicOutput,
    ExpectationResult,
    Materialization,
    Output,
    OutputDefinition,
)
from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.types.dagster_type import DagsterTypeKind, is_generic_output_annotation

from ..context.compute import OpExecutionContext


class NoAnnotationSentinel:
    pass


def create_solid_compute_wrapper(solid_def: OpDefinition):
    compute_fn = cast(DecoratedOpFunction, solid_def.compute_fn)
    fn = compute_fn.decorated_fn
    input_defs = solid_def.input_defs
    output_defs = solid_def.output_defs
    context_arg_provided = compute_fn.has_context_arg()
    config_arg_cls = compute_fn.get_config_arg().annotation if compute_fn.has_config_arg() else None
    resource_arg_mapping = {arg.name: arg.name for arg in compute_fn.get_resource_args()}

    input_names = [
        input_def.name
        for input_def in input_defs
        if not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ]

    @wraps(fn)
    def compute(context: OpExecutionContext, input_defs) -> Generator[Output, None, None]:
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
                return _coerce_async_solid_to_async_gen(result, context, output_defs)
            # already a generator
            return result
        else:
            # we have a regular function, do not execute it before we are in an iterator
            # (as we want all potential failures to happen inside iterators)
            return _coerce_solid_compute_fn_to_iterator(
                fn,
                output_defs,
                context,
                context_arg_provided,
                kwargs,
                config_arg_cls,
                resource_arg_mapping,
            )

    return compute


async def _coerce_async_solid_to_async_gen(awaitable, context, output_defs):
    result = await awaitable
    for event in validate_and_coerce_op_result_to_iterator(result, context, output_defs):
        yield event


def invoke_compute_fn(
    fn: Callable,
    context: OpExecutionContext,
    kwargs: Dict[str, Any],
    context_arg_provided: bool,
    config_arg_cls: Optional[Type[Config]],
    resource_args: Optional[Dict[str, str]] = None,
) -> Any:
    args_to_pass = kwargs
    if config_arg_cls:
        # config_arg_cls is either a Config class or a primitive type
        if issubclass(config_arg_cls, Config):
            args_to_pass["config"] = config_arg_cls(**context.op_config)
        else:
            args_to_pass["config"] = context.op_config
    if resource_args:
        for resource_name, arg_name in resource_args.items():
            args_to_pass[arg_name] = getattr(context.resources, resource_name)
    return fn(context, **args_to_pass) if context_arg_provided else fn(**args_to_pass)


def _coerce_solid_compute_fn_to_iterator(
    fn, output_defs, context, context_arg_provided, kwargs, config_arg_class, resource_arg_mapping
):
    result = invoke_compute_fn(
        fn, context, kwargs, context_arg_provided, config_arg_class, resource_arg_mapping
    )
    for event in validate_and_coerce_op_result_to_iterator(result, context, output_defs):
        yield event


def _zip_and_iterate_solid_result(
    result: Any, context: OpExecutionContext, output_defs: Sequence[OutputDefinition]
) -> Iterator[Tuple[int, Any, OutputDefinition]]:
    if len(output_defs) > 1:
        _validate_multi_return(context, result, output_defs)
        for position, (output_def, element) in enumerate(zip(output_defs, result)):
            yield position, output_def, element
    else:
        yield 0, output_defs[0], result


def _validate_multi_return(
    context: OpExecutionContext,
    result: Any,
    output_defs: Sequence[OutputDefinition],
) -> None:
    # When returning from an op with multiple outputs, the returned object must be a tuple of the same length as the number of outputs. At the time of the op's construction, we verify that a provided annotation is a tuple with the same length as the number of outputs, so if the result matches the number of output defs on the op, it will transitively also match the annotation.
    if not isinstance(result, tuple):
        raise DagsterInvariantViolationError(
            f"{context.describe_op()} has multiple outputs, but only one "
            f"output was returned of type {type(result)}. When using "
            "multiple outputs, either yield each output, or return a tuple "
            "containing a value for each output. Check out the "
            "documentation on outputs for more: "
            "https://docs.dagster.io/concepts/ops-jobs-graphs/ops#outputs."
        )
    output_tuple = cast(tuple, result)
    if not len(output_tuple) == len(output_defs):
        raise DagsterInvariantViolationError(
            "Length mismatch between returned tuple of outputs and number of "
            f"output defs on {context.describe_op()}. Output tuple has "
            f"{len(output_tuple)} outputs, while "
            f"{context.op_def.node_type_str} has {len(output_defs)} outputs."
        )


def _get_annotation_for_output_position(
    position: int, op_def: OpDefinition, output_defs: Sequence[OutputDefinition]
) -> Any:
    if op_def.is_from_decorator():
        if len(output_defs) > 1 and op_def.get_output_annotation() != inspect.Parameter.empty:
            return get_args(op_def.get_output_annotation())[position]
        else:
            return op_def.get_output_annotation()
    return NoAnnotationSentinel()


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
    result: Any, context: OpExecutionContext, output_defs: Sequence[OutputDefinition]
) -> Generator[Any, None, None]:
    if inspect.isgenerator(result):
        # this happens when a user explicitly returns a generator in the solid
        for event in result:
            yield event
    elif isinstance(result, (AssetMaterialization, Materialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: If you are "
            "returning an AssetMaterialization "
            "or an ExpectationResult from "
            f"{context.op_def.node_type_str} you must yield them "
            "directly, or log them using the OpExecutionContext.log_event method to avoid "
            "ambiguity with an implied result from returning a "
            "value. Check out the docs on logging events here: "
            "https://docs.dagster.io/concepts/ops-jobs-graphs/op-events#op-events-and-exceptions"
        )
    elif result is not None and not output_defs:
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: Unexpectedly returned output of type"
            f" {type(result)}. {context.op_def.node_type_str.capitalize()} is explicitly defined to"
            " return no results."
        )
    elif output_defs:
        for position, output_def, element in _zip_and_iterate_solid_result(
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
                    dynamic_output = cast(DynamicOutput, item)
                    _check_output_object_name(dynamic_output, output_def, position)

                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=DeprecationWarning)

                        yield DynamicOutput(
                            output_name=output_def.name,
                            value=dynamic_output.value,
                            mapping_key=dynamic_output.mapping_key,
                            metadata_entries=list(dynamic_output.metadata_entries),
                        )
            elif isinstance(element, Output):
                if annotation != inspect.Parameter.empty and not is_generic_output_annotation(
                    annotation
                ):
                    raise DagsterInvariantViolationError(
                        f"Error with output for {context.describe_op()}: received Output object for"
                        f" output '{output_def.name}' which does not have an Output annotation."
                        f" Annotation has type {annotation}."
                    )
                output = cast(Output, element)
                _check_output_object_name(output, output_def, position)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=DeprecationWarning)

                    yield Output(
                        output_name=output_def.name,
                        value=output.value,
                        metadata_entries=output.metadata_entries,
                    )
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
                    context.log.warn(
                        'Value "None" returned for non-required output '
                        f'"{output_def.name}" of {context.describe_op()}. '
                        "This value will be passed to downstream "
                        f"{context.op_def.node_type_str}s. For conditional "
                        "execution, results must be yielded: "
                        "https://docs.dagster.io/concepts/ops-jobs-graphs/graphs#with-conditional-branching"
                    )
                yield Output(output_name=output_def.name, value=element)
