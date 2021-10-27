import inspect
from functools import wraps
from typing import Generator, cast

from dagster import check
from dagster.core.definitions import (
    AssetMaterialization,
    ExpectationResult,
    Materialization,
    Output,
    SolidDefinition,
)
from dagster.core.definitions.decorators.solid import DecoratedSolidFunction
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.types.dagster_type import DagsterTypeKind


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
    for event in _validate_and_coerce_solid_result_to_iterator(result, context, output_defs):
        yield event


def _coerce_solid_compute_fn_to_iterator(fn, output_defs, context, context_arg_provided, kwargs):
    result = fn(context, **kwargs) if context_arg_provided else fn(**kwargs)
    for event in _validate_and_coerce_solid_result_to_iterator(result, context, output_defs):
        yield event


def _validate_and_coerce_solid_result_to_iterator(result, context, output_defs):

    if isinstance(result, (AssetMaterialization, Materialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            (
                "Error in {described_op}: If you are returning an AssetMaterialization "
                "or an ExpectationResult from {node_type} you must yield them to avoid "
                "ambiguity with an implied result from returning a value.".format(
                    described_op=context.describe_op(),
                    node_type=context.solid_def.node_type_str,
                )
            )
        )

    if inspect.isgenerator(result):
        # this happens when a user explicitly returns a generator in the solid
        for event in result:
            yield event
    elif isinstance(result, Output):
        yield result
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

        for output_defs, element in zip(output_defs, result):
            yield Output(output_name=output_defs.name, value=element)
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
