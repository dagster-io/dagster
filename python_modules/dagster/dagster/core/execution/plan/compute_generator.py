import inspect
from functools import wraps
from typing import Any, Generator, Iterator, Sequence, Tuple, Union, cast

import dagster._check as check
from dagster.core.definitions import (
    AssetMaterialization,
    DynamicOutput,
    ExpectationResult,
    Materialization,
    Output,
    OutputDefinition,
    SolidDefinition,
)
from dagster.core.definitions.decorators.solid_decorator import DecoratedSolidFunction
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.types.dagster_type import (
    DagsterTypeKind,
    is_dynamic_output_annotation,
    is_generic_output_annotation,
)
from dagster.seven.typing import get_args, get_origin

from ..context.compute import OpExecutionContext


class NoAnnotationSentinel:
    pass


def create_solid_compute_wrapper(solid_def: SolidDefinition):
    compute_fn = cast(DecoratedSolidFunction, solid_def.compute_fn)
    fn = compute_fn.decorated_fn
    input_defs = solid_def.input_defs
    output_defs = solid_def.output_defs
    context_arg_provided = compute_fn.has_context_arg()

    input_names = [
        input_def.name
        for input_def in input_defs
        if not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ]

    @wraps(fn)
    def compute(context, input_defs) -> Generator[Output, None, None]:
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        if (
            inspect.isgeneratorfunction(fn)
            or inspect.isasyncgenfunction(fn)
            or inspect.iscoroutinefunction(fn)
        ):
            # safe to execute the function, as doing so will not immediately execute user code
            result = fn(context, **kwargs) if context_arg_provided else fn(**kwargs)
            if inspect.iscoroutine(result):
                return _coerce_async_solid_to_async_gen(result, context, output_defs)
            # already a generator
            return result
        else:
            # we have a regular function, do not execute it before we are in an iterator
            # (as we want all potential failures to happen inside iterators)
            return _coerce_solid_compute_fn_to_iterator(
                fn, output_defs, context, context_arg_provided, kwargs
            )

    return compute


async def _coerce_async_solid_to_async_gen(awaitable, context, output_defs):
    result = await awaitable
    for event in validate_and_coerce_solid_result_to_iterator(result, context, output_defs):
        yield event


def _coerce_solid_compute_fn_to_iterator(fn, output_defs, context, context_arg_provided, kwargs):
    result = fn(context, **kwargs) if context_arg_provided else fn(**kwargs)
    for event in validate_and_coerce_solid_result_to_iterator(result, context, output_defs):
        yield event


def _zip_and_iterate_solid_result(
    result: Any, context: OpExecutionContext, output_defs: Sequence[OutputDefinition]
) -> Iterator[Tuple[int, Any, OutputDefinition]]:
    if len(output_defs) > 1:
        if (
            context.solid_def.is_from_decorator()
            and context.solid_def.compute_fn.get_output_annotation()
            and get_origin(context.solid_def.get_output_annotation()) == tuple
        ):
            for position, (output_def, element) in enumerate(zip(output_defs, result)):
                yield position, output_def, element
        else:
            raise DagsterInvariantViolationError(
                f"{context.describe_op()} has multiple outputs, but only one "
                f"output was returned of type {type(result)}. When using "
                "multiple outputs, either yield each output, or return a tuple "
                "containing a value for each output. Check out the "
                "documentation on outputs for more: "
                "https://docs.dagster.io/concepts/ops-jobs-graphs/ops#outputs."
            )
    else:
        yield 0, output_defs[0], result


def _get_annotation_for_output_position(
    position: int, solid_def: SolidDefinition, output_defs: Sequence[OutputDefinition]
) -> Any:
    if solid_def.is_from_decorator():
        if len(output_defs) > 1:
            return get_args(solid_def.get_output_annotation())[position]
        else:
            return solid_def.get_output_annotation()
    return NoAnnotationSentinel()


def _check_output_object_name(
    output: Union[DynamicOutput, Output], output_def: OutputDefinition, position: int
) -> None:
    from dagster.core.definitions.events import DEFAULT_OUTPUT

    if not output.output_name == DEFAULT_OUTPUT and not output.output_name == output_def.name:
        raise DagsterInvariantViolationError(
            f"Bad state: Output was explicitly named '{output.output_name}', "
            "which does not match the output definition specified for position "
            f"{position}: '{output_def.name}'."
        )


def validate_and_coerce_solid_result_to_iterator(
    result: Any, context: OpExecutionContext, output_defs: Sequence[OutputDefinition]
) -> Generator[Any, None, None]:
    if inspect.isgenerator(result):
        # this happens when a user explicitly returns a generator in the solid
        for event in result:
            yield event
    elif result is not None and not output_defs:
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: Unexpectedly returned output of "
            f"type {type(result)}. {context.solid_def.node_type_str.capitalize()} is explicitly defined to return no "
            "results."
        )
    else:
        for position, output_def, element in _zip_and_iterate_solid_result(
            result, context, output_defs
        ):
            annotation = _get_annotation_for_output_position(
                position, context.solid_def, output_defs
            )
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
                            f"dynamic output '{output_def.name}' expected a "
                            "list of DynamicOutput objects, but received an "
                            f"item with type {type(item)}."
                        )
                    dynamic_output = cast(DynamicOutput, item)
                    _check_output_object_name(dynamic_output, output_def, position)
                    yield DynamicOutput(
                        output_name=output_def.name,
                        value=dynamic_output.value,
                        mapping_key=dynamic_output.mapping_key,
                        metadata_entries=dynamic_output.metadata_entries,
                    )
            elif is_generic_output_annotation(annotation):
                if not isinstance(element, Output):
                    raise DagsterInvariantViolationError(
                        f"Error with output for {context.describe_op()}: output "
                        f"'{output_def.name}' has generic output annotation, "
                        "but did not receive an Output object for this output. "
                        f"Received instead an object of type {type(element)}."
                    )
                output = cast(Output, element)
                _check_output_object_name(output, output_def, position)
                yield Output(
                    output_name=output_def.name,
                    value=output.value,
                    metadata_entries=output.metadata_entries,
                )
            else:
                if isinstance(element, (AssetMaterialization, Materialization, ExpectationResult)):
                    raise DagsterInvariantViolationError(
                        f"Error in {context.describe_op()}: If you are "
                        "returning an AssetMaterialization "
                        f"or an ExpectationResult from "
                        f"{context.solid_def.node_type_str} you must yield them "
                        "directly, or log them using the OpExecutionContext.log_event method to avoid "
                        "ambiguity with an implied result from returning a "
                        "value. Check out the docs on logging events here: "
                        "https://docs.dagster.io/concepts/ops-jobs-graphs/op-events#op-events-and-exceptions"
                    )
                if isinstance(element, (Output, DynamicOutput)):
                    raise DagsterInvariantViolationError(
                        f"Error in {context.describe_op()}: Output object "
                        "returned directly without annotating the decorated "
                        "function. Output events can either be yielded, or "
                        "returned with an accompanying annotation. Check out "
                        "the docs on specifying Output annotations here: "
                        "https://docs.dagster.io/concepts/ops-jobs-graphs/op-events#output-objects"
                    )
                if result is None and output_def.is_required is False:
                    context.log.warn(
                        'Value "None" returned for non-required output '
                        f'"{output_def.name}" of {context.describe_op()}. '
                        "This value will be passed to downstream "
                        f"{context.solid_def.node_type_str}s. For conditional "
                        "execution, results must be yielded: "
                        "https://docs.dagster.io/concepts/ops-jobs-graphs/graphs#with-conditional-branching"
                    )
                # If an output object was not returned, then construct one from any metadata that has been logged within the op's body.
                metadata = context.get_output_metadata(output_def.name)
                yield Output(output_name=output_def.name, value=element, metadata=metadata)


def _validate_and_coerce_solid_result_to_iterator_old(
    result: Any, context: OpExecutionContext, output_defs: Sequence[OutputDefinition]
):
    from dagster.core.definitions.events import DEFAULT_OUTPUT

    if isinstance(result, (AssetMaterialization, Materialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            f"Error in {context.describe_op()}: If you are returning an AssetMaterialization "
            f"or an ExpectationResult from {context.solid_def.node_type_str} you must yield them directly, or log them using the OpExecutionContext.log_event method to avoid "
            "ambiguity with an implied result from returning a value."
        )

    if inspect.isgenerator(result):
        # this happens when a user explicitly returns a generator in the solid
        for event in result:
            yield event
    elif isinstance(result, Output):
        yield result
    elif isinstance(result, DynamicOutput):
        raise DagsterInvariantViolationError(
            f"Attempted to directly return a DynamicOutput from {context.describe_op()}. DynamicOutput objects must be either yielded or returned in a list."
        )
    elif len(output_defs) == 1 and output_defs[0].is_dynamic:
        if isinstance(result, list) and all([isinstance(event, DynamicOutput) for event in result]):
            for event in result:
                yield event
        elif result is not None:
            check.failed(
                f"{context.describe_op()} has a single dynamic output named '{output_defs[0].name}', which expects either a list of DynamicOutputs to be returned, or DynamicOutput objects to be yielded. Received instead an object of type {type(result)}"
            )
    elif len(output_defs) == 1:
        if result is None and output_defs[0].is_required is False:
            context.log.warn(
                'Value "None" returned for non-required output "{output_name}" of {described_op}. '
                "This value will be passed to downstream {node_type}s. For conditional execution use\n"
                '  yield Output(value, "{output_name}")\n'
                "when you want the downstream {node_type}s to execute, "
                "and do not yield it when you want downstream solids to skip.".format(
                    output_name=output_defs[0].name,
                    described_op=context.describe_op(),
                    node_type=context.solid_def.node_type_str,
                )
            )
        yield Output(value=result, output_name=output_defs[0].name)
    elif len(output_defs) > 1 and isinstance(result, tuple):
        if len(result) != len(output_defs):
            check.failed(
                f"Solid '{context.solid_name}' has {len(output_defs)} output definitions, but "
                f"returned a tuple with {len(result)} elements"
            )

        for position, (output_def, element) in enumerate(zip(output_defs, result)):
            # If an output object was provided directly, ensure that it matches
            # with expected order from provided output definitions.
            if isinstance(element, Output):
                # If a name was explicitly provided on the output object, and
                # that name does not match the name expected at this position,
                # then throw an error.
                if (
                    not element.output_name == DEFAULT_OUTPUT
                    and not element.output_name == output_def.name
                ):
                    raise DagsterInvariantViolationError(
                        f"Bad state: Received a tuple of outputs. An output was "
                        f"explicitly named '{element.output_name}', which does "
                        "not match the output definition specified for "
                        f"position {position}: '{output_def.name}'."
                    )
                yield Output(
                    output_name=output_def.name,
                    value=element.value,
                    metadata_entries=element.metadata_entries,
                )
            elif (
                isinstance(element, list)
                and element  # ensure list is non empty before all() check
                and all([isinstance(event, DynamicOutput) for event in element])
            ):
                if not output_def.is_dynamic:
                    raise DagsterInvariantViolationError(
                        f"Received a list of DynamicOutputs for output named '{output_def.name}', but output is not dynamic."
                    )
                for dynamic_output in element:
                    if (
                        not dynamic_output.output_name == DEFAULT_OUTPUT
                        and not dynamic_output.output_name == output_def.name
                    ):
                        raise DagsterInvariantViolationError(
                            f"Bad state: Received a tuple of outputs. An output was "
                            f"explicitly named '{dynamic_output.output_name}', which does "
                            "not match the dynamic output definition specified for "
                            f"position {position}: '{output_def.name}'."
                        )
                    yield DynamicOutput(
                        output_name=output_def.name,
                        value=dynamic_output.value,
                        mapping_key=dynamic_output.mapping_key,
                        metadata_entries=dynamic_output.metadata_entries,
                    )
            # if we got an empty list and its dynamic output, yield nothing
            elif isinstance(element, list) and not element and output_def.is_dynamic:
                continue
            else:
                # If an output object was not returned, then construct one from any metadata that has been logged within the op's body.
                metadata = context.get_output_metadata(output_def.name)
                yield Output(output_name=output_def.name, value=element, metadata=metadata)
    elif result is not None:
        if not output_defs:
            raise DagsterInvariantViolationError(
                (
                    "Error in {described_op}: Unexpectedly returned output {result} "
                    "of type {type_}. {node_type} is explicitly defined to return no "
                    "results."
                ).format(
                    described_op=context.describe_op(),
                    result=result,
                    type_=type(result),
                    node_type=context.solid_def.node_type_str.capitalize(),
                )
            )

        raise DagsterInvariantViolationError(
            (
                "Error in {described_op}: {node_type} unexpectedly returned "
                "output {result} of type {type_}. Should "
                "be a generator, containing or yielding "
                "{n_results} results: {{{expected_results}}}."
            ).format(
                described_op=context.describe_op(),
                node_type=context.solid_def.node_type_str,
                result=result,
                type_=type(result),
                n_results=len(output_defs),
                expected_results=", ".join(
                    [
                        "'{result_name}': {dagster_type}".format(
                            result_name=output_def.name,
                            dagster_type=output_def.dagster_type,
                        )
                        for output_def in output_defs
                    ]
                ),
            )
        )
