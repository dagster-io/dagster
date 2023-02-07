import inspect
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import dagster._check as check
from dagster._core.errors import (
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
)

from .events import (
    AssetMaterialization,
    AssetObservation,
    DynamicOutput,
    ExpectationResult,
    Materialization,
    Output,
)
from .output import DynamicOutputDefinition

if TYPE_CHECKING:
    from ..execution.context.invocation import BoundOpExecutionContext, UnboundOpExecutionContext
    from .composition import PendingNodeInvocation
    from .decorators.solid_decorator import DecoratedOpFunction
    from .op_definition import OpDefinition
    from .output import OutputDefinition


def op_invocation_result(
    op_def_or_invocation: Union["OpDefinition", "PendingNodeInvocation"],
    context: Optional["UnboundOpExecutionContext"],
    *args,
    **kwargs,
) -> Any:
    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction
    from dagster._core.execution.context.invocation import build_solid_context

    from .composition import PendingNodeInvocation

    op_def = (
        op_def_or_invocation.node_def.ensure_op_def()
        if isinstance(op_def_or_invocation, PendingNodeInvocation)
        else op_def_or_invocation
    )

    _check_invocation_requirements(op_def, context)

    bound_context = (context or build_solid_context()).bind(op_def_or_invocation)

    input_dict = _resolve_inputs(op_def, args, kwargs, bound_context)

    compute_fn = op_def.compute_fn
    if not isinstance(compute_fn, DecoratedOpFunction):
        check.failed("solid invocation only works with decorated solid fns")

    compute_fn = cast(DecoratedOpFunction, compute_fn)

    from ..execution.plan.compute_generator import invoke_compute_fn

    result = invoke_compute_fn(
        compute_fn.decorated_fn,
        bound_context,
        input_dict,
        compute_fn.has_context_arg(),
        compute_fn.get_config_arg().annotation if compute_fn.has_config_arg() else None,
    )

    return _type_check_output_wrapper(op_def, result, bound_context)


def _check_invocation_requirements(
    solid_def: "OpDefinition", context: Optional["UnboundOpExecutionContext"]
) -> None:
    """Ensure that provided context fulfills requirements of solid definition.

    If no context was provided, then construct an enpty UnboundSolidExecutionContext
    """
    # Check resource requirements
    if (
        solid_def.required_resource_keys
        and cast("DecoratedOpFunction", solid_def.compute_fn).has_context_arg()
        and context is None
    ):
        node_label = solid_def.node_type_str  # string "solid" for solids, "op" for ops
        raise DagsterInvalidInvocationError(
            f'{node_label} "{solid_def.name}" has required resources, but no context was provided.'
            f" Use the `build_{node_label}_context` function to construct a context with the"
            " required resources."
        )

    # Check config requirements
    if not context and solid_def.config_schema.as_field().is_required:
        node_label = solid_def.node_type_str  # string "solid" for solids, "op" for ops
        raise DagsterInvalidInvocationError(
            f'{node_label} "{solid_def.name}" has required config schema, but no context was'
            f" provided. Use the `build_{node_label}_context` function to create a context with"
            " config."
        )


def _resolve_inputs(solid_def: "OpDefinition", args, kwargs, context: "BoundOpExecutionContext"):
    from dagster._core.execution.plan.execute_step import do_type_check

    nothing_input_defs = [
        input_def for input_def in solid_def.input_defs if input_def.dagster_type.is_nothing
    ]

    # Check kwargs for nothing inputs, and error if someone provided one.
    for input_def in nothing_input_defs:
        if input_def.name in kwargs:
            node_label = solid_def.node_type_str  # string "solid" for solids, "op" for ops

            raise DagsterInvalidInvocationError(
                f"Attempted to provide value for nothing input '{input_def.name}'. Nothing "
                f"dependencies are ignored when directly invoking {node_label}s."
            )

    # Discard nothing dependencies - we ignore them during invocation.
    input_defs_by_name = {
        input_def.name: input_def
        for input_def in solid_def.input_defs
        if not input_def.dagster_type.is_nothing
    }

    # Fail early if too many inputs were provided.
    if len(input_defs_by_name) < len(args) + len(kwargs):
        if len(nothing_input_defs) > 0:
            suggestion = (
                "This may be because you attempted to provide a value for a nothing "
                "dependency. Nothing dependencies are ignored when directly invoking ops."
            )
        else:
            suggestion = (
                "This may be because an argument was provided for the context parameter, "
                "but no context parameter was defined for the op."
            )

        node_label = solid_def.node_type_str
        raise DagsterInvalidInvocationError(
            f"Too many input arguments were provided for {node_label} '{context.alias}'."
            f" {suggestion}"
        )

    # If more args were provided than the function has positional args, then fail early.
    positional_inputs = cast("DecoratedOpFunction", solid_def.compute_fn).positional_inputs()
    if len(args) > len(positional_inputs):
        raise DagsterInvalidInvocationError(
            f"{solid_def.node_type_str} '{solid_def.name}' has {len(positional_inputs)} positional"
            f" inputs, but {len(args)} positional inputs were provided."
        )

    input_dict = {}

    for position, value in enumerate(args):
        input_dict[positional_inputs[position]] = value

    for positional_input in positional_inputs[len(args) :]:
        input_def = input_defs_by_name[positional_input]

        if not input_def.has_default_value and positional_input not in kwargs:
            raise DagsterInvalidInvocationError(
                f'No value provided for required input "{positional_input}".'
            )

        input_dict[positional_input] = (
            kwargs[positional_input] if positional_input in kwargs else input_def.default_value
        )

    unassigned_kwargs = {k: v for k, v in kwargs.items() if k not in input_dict}
    # If there are unassigned inputs, then they may be intended for use with a variadic keyword argument.
    if unassigned_kwargs and cast("DecoratedOpFunction", solid_def.compute_fn).has_var_kwargs():
        for k, v in unassigned_kwargs.items():
            input_dict[k] = v

    # Type check inputs
    op_label = context.describe_op()

    for input_name, val in input_dict.items():
        input_def = input_defs_by_name[input_name]
        dagster_type = input_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, val)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for {op_label} input "{input_def.name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )

    return input_dict


def _type_check_output_wrapper(
    solid_def: "OpDefinition", result: Any, context: "BoundOpExecutionContext"
) -> Any:
    """Type checks and returns the result of a solid.

    If the solid result is itself a generator, then wrap in a fxn that will type check and yield
    outputs.
    """
    output_defs = {output_def.name: output_def for output_def in solid_def.output_defs}

    # Async generator case
    if inspect.isasyncgen(result):

        async def to_gen(async_gen):
            outputs_seen = set()

            async for event in async_gen:
                if isinstance(
                    event,
                    (AssetMaterialization, AssetObservation, Materialization, ExpectationResult),
                ):
                    yield event
                else:
                    if not isinstance(event, (Output, DynamicOutput)):
                        raise DagsterInvariantViolationError(
                            f"When yielding outputs from a {solid_def.node_type_str} generator,"
                            " they should be wrapped in an `Output` object."
                        )
                    else:
                        output_def = output_defs[event.output_name]
                        _type_check_output(output_def, event, context)
                        if output_def.name in outputs_seen and not isinstance(
                            output_def, DynamicOutputDefinition
                        ):
                            raise DagsterInvariantViolationError(
                                f"Invocation of {solid_def.node_type_str} '{context.alias}' yielded"
                                f" an output '{output_def.name}' multiple times."
                            )
                        outputs_seen.add(output_def.name)
                    yield event
            for output_def in solid_def.output_defs:
                if output_def.name not in outputs_seen and output_def.is_required:
                    raise DagsterInvariantViolationError(
                        f"Invocation of {solid_def.node_type_str} '{context.alias}' did not return"
                        f" an output for non-optional output '{output_def.name}'"
                    )

        return to_gen(result)

    # Coroutine result case
    elif inspect.iscoroutine(result):

        async def type_check_coroutine(coro):
            out = await coro
            return _type_check_function_output(solid_def, out, context)

        return type_check_coroutine(result)

    # Regular generator case
    elif inspect.isgenerator(result):

        def type_check_gen(gen):
            outputs_seen = set()
            for event in gen:
                if isinstance(
                    event,
                    (AssetMaterialization, AssetObservation, Materialization, ExpectationResult),
                ):
                    yield event
                else:
                    if not isinstance(event, (Output, DynamicOutput)):
                        raise DagsterInvariantViolationError(
                            f"When yielding outputs from a {solid_def.node_type_str} generator,"
                            " they should be wrapped in an `Output` object."
                        )
                    else:
                        output_def = output_defs[event.output_name]
                        output = _type_check_output(output_def, event, context)
                        if output_def.name in outputs_seen and not isinstance(
                            output_def, DynamicOutputDefinition
                        ):
                            raise DagsterInvariantViolationError(
                                f"Invocation of {solid_def.node_type_str} '{context.alias}' yielded"
                                f" an output '{output_def.name}' multiple times."
                            )
                        outputs_seen.add(output_def.name)
                    yield output
            for output_def in solid_def.output_defs:
                if (
                    output_def.name not in outputs_seen
                    and output_def.is_required
                    and not output_def.is_dynamic
                ):
                    raise DagsterInvariantViolationError(
                        f"Invocation of {solid_def.node_type_str} '{context.alias}' did not return"
                        f" an output for non-optional output '{output_def.name}'"
                    )

        return type_check_gen(result)

    # Non-generator case
    return _type_check_function_output(solid_def, result, context)


def _type_check_function_output(
    op_def: "OpDefinition", result: Any, context: "BoundOpExecutionContext"
):
    from ..execution.plan.compute_generator import validate_and_coerce_op_result_to_iterator

    output_defs_by_name = {output_def.name: output_def for output_def in op_def.output_defs}
    for event in validate_and_coerce_op_result_to_iterator(result, context, op_def.output_defs):
        _type_check_output(output_defs_by_name[event.output_name], event, context)
    return result


def _type_check_output(
    output_def: "OutputDefinition", output: Any, context: "BoundOpExecutionContext"
) -> Any:
    """Validates and performs core type check on a provided output.

    Args:
        output_def (OutputDefinition): The output definition to validate against.
        output (Any): The output to validate.
        context (BoundSolidExecutionContext): Context containing resources to be used for type
            check.
    """
    from ..execution.plan.execute_step import do_type_check

    op_label = context.describe_op()

    if isinstance(output, (Output, DynamicOutput)):
        dagster_type = output_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, output.value)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for {op_label} output "{output.output_name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )

        context.observe_output(
            output_def.name, output.mapping_key if isinstance(output, DynamicOutput) else None
        )
        return output
    else:
        dagster_type = output_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, output)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for {op_label} output "{output_def.name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )
        return output
