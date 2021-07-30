import inspect
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster import check
from dagster.core.errors import (
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
)

from .events import AssetMaterialization, ExpectationResult, Materialization, Output

if TYPE_CHECKING:
    from .solid import SolidDefinition
    from .output import OutputDefinition
    from .composition import PendingNodeInvocation
    from ..execution.context.invocation import (
        BoundSolidExecutionContext,
        UnboundSolidExecutionContext,
    )


def solid_invocation_result(
    solid_def_or_invocation: Union["SolidDefinition", "PendingNodeInvocation"],
    context: Optional["UnboundSolidExecutionContext"],
    *args,
    **kwargs,
) -> Any:
    from dagster.core.execution.context.invocation import build_solid_context
    from dagster.core.definitions.decorators.solid import DecoratedSolidFunction
    from .composition import PendingNodeInvocation

    solid_def = (
        solid_def_or_invocation.node_def.ensure_solid_def()
        if isinstance(solid_def_or_invocation, PendingNodeInvocation)
        else solid_def_or_invocation
    )

    _check_invocation_requirements(solid_def, context)

    context = (context or build_solid_context()).bind(solid_def_or_invocation)

    input_dict = _resolve_inputs(solid_def, args, kwargs, context)

    compute_fn = solid_def.compute_fn
    if not isinstance(compute_fn, DecoratedSolidFunction):
        check.failed("solid invocation only works with decorated solid fns")

    result = (
        compute_fn.decorated_fn(context, **input_dict)
        if compute_fn.has_context_arg()
        else compute_fn.decorated_fn(**input_dict)
    )

    return _type_check_output_wrapper(solid_def, result, context)


def _check_invocation_requirements(
    solid_def: "SolidDefinition", context: Optional["UnboundSolidExecutionContext"]
) -> None:
    """Ensure that provided context fulfills requirements of solid definition.

    If no context was provided, then construct an enpty UnboundSolidExecutionContext
    """

    # Check resource requirements
    if solid_def.required_resource_keys and context is None:
        raise DagsterInvalidInvocationError(
            f'Solid "{solid_def.name}" has required resources, but no context was provided. Use the'
            "`build_solid_context` function to construct a context with the required "
            "resources."
        )

    # Check config requirements
    if not context and solid_def.config_schema.as_field().is_required:
        raise DagsterInvalidInvocationError(
            f'Solid "{solid_def.name}" has required config schema, but no context was provided. '
            "Use the `build_solid_context` function to create a context with config."
        )


def _resolve_inputs(
    solid_def: "SolidDefinition", args, kwargs, context: "BoundSolidExecutionContext"
):
    from dagster.core.execution.plan.execute_step import do_type_check

    input_defs = solid_def.input_defs

    # Fail early if too many inputs were provided.
    if len(input_defs) < len(args) + len(kwargs):
        raise DagsterInvalidInvocationError(
            f"Too many input arguments were provided for solid '{context.alias}'. This may be because "
            "an argument was provided for the context parameter, but no context parameter was defined "
            "for the solid."
        )

    input_dict = {
        input_def.name: input_val for input_val, input_def in zip(args, input_defs[: len(args)])
    }

    for input_def in input_defs[len(args) :]:
        if not input_def.has_default_value and input_def.name not in kwargs:
            raise DagsterInvalidInvocationError(
                f'No value provided for required input "{input_def.name}".'
            )

        input_dict[input_def.name] = (
            kwargs[input_def.name] if input_def.name in kwargs else input_def.default_value
        )

    # Type check inputs
    input_defs_by_name = {input_def.name: input_def for input_def in input_defs}
    for input_name, val in input_dict.items():

        input_def = input_defs_by_name[input_name]
        dagster_type = input_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, val)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for solid input "{input_def.name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )

    return input_dict


def _type_check_output_wrapper(
    solid_def: "SolidDefinition", result: Any, context: "BoundSolidExecutionContext"
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
                if isinstance(event, (AssetMaterialization, Materialization, ExpectationResult)):
                    yield event
                else:
                    if not isinstance(event, Output):
                        raise DagsterInvariantViolationError(
                            "When yielding outputs from a solid generator, they should be wrapped in an `Output` object."
                        )
                    else:
                        output_def = output_defs[event.output_name]
                        _type_check_output(output_def, event, context)
                        if output_def.name in outputs_seen:
                            raise DagsterInvariantViolationError(
                                f"Invocation of solid '{context.alias}' yielded an output '{output_def.name}' multiple times."
                            )
                        outputs_seen.add(output_def.name)
                    yield event
            for output_def in solid_def.output_defs:
                if output_def.name not in outputs_seen and output_def.is_required:
                    raise DagsterInvariantViolationError(
                        f"Invocation of solid '{context.alias}' did not return an output for non-optional output '{output_def.name}'"
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
                if isinstance(event, (AssetMaterialization, Materialization, ExpectationResult)):
                    yield event
                else:
                    if not isinstance(event, Output):
                        raise DagsterInvariantViolationError(
                            "When yielding outputs from a solid generator, they should be wrapped in an `Output` object."
                        )
                    else:
                        output_def = output_defs[event.output_name]
                        output = _type_check_output(output_def, event, context)
                        if output_def.name in outputs_seen:
                            raise DagsterInvariantViolationError(
                                f"Invocation of solid '{context.alias}' yielded an output '{output_def.name}' multiple times."
                            )
                        outputs_seen.add(output_def.name)
                    yield output
            for output_def in solid_def.output_defs:
                if output_def.name not in outputs_seen and output_def.is_required:
                    raise DagsterInvariantViolationError(
                        f"Invocation of solid '{context.alias}' did not return an output for non-optional output '{output_def.name}'"
                    )

        return type_check_gen(result)

    # Non-generator case
    return _type_check_function_output(solid_def, result, context)


def _type_check_function_output(
    solid_def: "SolidDefinition", result: Any, context: "BoundSolidExecutionContext"
) -> Any:
    """Unpacks valid outputs from solid function."""

    if isinstance(result, (AssetMaterialization, Materialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            (
                f"Error in solid {solid_def.name}: If you are returning an AssetMaterialization "
                "or an ExpectationResult from solid you must yield them to avoid "
                "ambiguity with an implied result from returning a value."
            )
        )
    if (
        not isinstance(result, Output)
        and isinstance(result, tuple)
        and len(solid_def.output_defs) > 1
    ):  # for op case
        for i, output_def in enumerate(solid_def.output_defs):
            _type_check_output(output_def, result[i], context)
        return result

    if len(solid_def.output_defs) > 1 and not isinstance(result, Output):
        raise DagsterInvariantViolationError(
            "Multiple output definitions but no Output wrapper provided is ambiguous."
        )
    received_output = None
    output_defs = {output_def.name: output_def for output_def in solid_def.output_defs}
    if isinstance(result, Output):
        if result.output_name not in output_defs:
            raise DagsterInvariantViolationError(
                f'Invocation of solid "{solid_def.name}" returned an output "{result.output_name}" '
                "that does not exist. The available outputs are "
                f"{[output_def.name for output_def in solid_def.output_defs]}"
            )
        output_def = output_defs[result.output_name]
        received_output = output_def.name
        _type_check_output(output_def, result, context)
    else:
        _type_check_output(solid_def.output_defs[0], result, context)
        received_output = solid_def.output_defs[0].name

    for output_def in solid_def.output_defs:
        if output_def.is_required and not output_def.name == received_output:
            raise DagsterInvariantViolationError(
                f"Invocation of solid '{solid_def.name}' did not return an output for non-optional "
                f"output '{output_def.name}'."
            )
    return result


def _type_check_output(
    output_def: "OutputDefinition", output: Any, context: "BoundSolidExecutionContext"
) -> Any:
    """Validates and performs core type check on a provided output.

    Args:
        output_def (OutputDefinition): The output definition to validate against.
        output (Any): The output to validate.
        context (BoundSolidExecutionContext): Context containing resources to be used for type
            check.
    """
    from ..execution.plan.execute_step import do_type_check

    if isinstance(output, Output):
        dagster_type = output_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, output.value)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for solid output "{output.output_name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )
        return output
    else:
        dagster_type = output_def.dagster_type
        type_check = do_type_check(context.for_type(dagster_type), dagster_type, output)
        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description=(
                    f'Type check failed for solid output "{output_def.name}" - '
                    f'expected type "{dagster_type.display_name}". '
                    f"Description: {type_check.description}"
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=dagster_type,
            )
        return output
