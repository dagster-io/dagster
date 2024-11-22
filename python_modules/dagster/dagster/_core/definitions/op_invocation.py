import inspect
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar, Union, cast

import dagster._check as check
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.events import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DynamicOutput,
    ExpectationResult,
    Output,
)
from dagster._core.definitions.output import DynamicOutputDefinition, OutputDefinition
from dagster._core.definitions.result import AssetResult
from dagster._core.errors import (
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
)

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.composition import PendingNodeInvocation
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.execution.context.compute import OpExecutionContext
    from dagster._core.execution.context.invocation import BaseDirectExecutionContext

T = TypeVar("T")


class SeparatedArgsKwargs(NamedTuple):
    input_args: tuple[Any, ...]
    input_kwargs: dict[str, Any]
    resources_by_param_name: dict[str, Any]
    config_arg: Any


def _separate_args_and_kwargs(
    compute_fn: "DecoratedOpFunction",
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    resource_arg_mapping: dict[str, Any],
) -> SeparatedArgsKwargs:
    """Given a decorated compute function, a set of args and kwargs, and set of resource param names,
    separates the set of resource inputs from op/asset inputs returns a tuple of the categorized
    args and kwargs.

    We use the remaining args and kwargs to cleanly invoke the compute function, and we use the
    extracted resource inputs to populate the execution context.
    """
    resources_from_args_and_kwargs = {}
    params = get_function_params(compute_fn.decorated_fn)

    adjusted_args = []

    params_without_context = params[1:] if compute_fn.has_context_arg() else params

    config_arg = kwargs.get("config")

    # Get any (non-kw) args that correspond to resource inputs & strip them from the args list
    for i, arg in enumerate(args):
        param = params_without_context[i] if i < len(params_without_context) else None
        if param and param.kind != inspect.Parameter.KEYWORD_ONLY:
            if param.name in resource_arg_mapping:
                resources_from_args_and_kwargs[param.name] = arg
                continue
            if param.name == "config":
                config_arg = arg
                continue

        adjusted_args.append(arg)

    # Get any kwargs that correspond to resource inputs & strip them from the kwargs dict
    for resource_arg in resource_arg_mapping:
        if resource_arg in kwargs:
            resources_from_args_and_kwargs[resource_arg] = kwargs[resource_arg]

    adjusted_kwargs = {
        k: v for k, v in kwargs.items() if k not in resources_from_args_and_kwargs and k != "config"
    }

    return SeparatedArgsKwargs(
        input_args=tuple(adjusted_args),
        input_kwargs=adjusted_kwargs,
        resources_by_param_name=resources_from_args_and_kwargs,
        config_arg=config_arg,
    )


def _get_op_context(
    context,
) -> "OpExecutionContext":
    from dagster._core.execution.context.compute import AssetExecutionContext

    if isinstance(context, AssetExecutionContext):
        return context.op_execution_context
    return context


def direct_invocation_result(
    def_or_invocation: Union[
        "OpDefinition", "PendingNodeInvocation[OpDefinition]", "AssetsDefinition"
    ],
    *args,
    **kwargs,
) -> Any:
    from dagster._config.pythonic_config import Config
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.composition import PendingNodeInvocation
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.execution.context.invocation import (
        BaseDirectExecutionContext,
        build_op_context,
    )
    from dagster._core.execution.plan.compute_generator import invoke_compute_fn

    if isinstance(def_or_invocation, OpDefinition):
        op_def = def_or_invocation
        pending_invocation = None
        assets_def = None
    elif isinstance(def_or_invocation, AssetsDefinition):
        assets_def = def_or_invocation
        op_def = assets_def.op
        pending_invocation = None
    elif isinstance(def_or_invocation, PendingNodeInvocation):
        pending_invocation = def_or_invocation
        op_def = def_or_invocation.node_def
        assets_def = None
    else:
        check.failed(f"unexpected direct invocation target {def_or_invocation}")

    compute_fn = op_def.compute_fn
    if not isinstance(compute_fn, DecoratedOpFunction):
        raise DagsterInvalidInvocationError(
            "Attempted to directly invoke an op/asset that was not constructed using the `@op` or"
            " `@asset` decorator. Only decorated functions can be directly invoked."
        )

    context = None
    if compute_fn.has_context_arg():
        if len(args) + len(kwargs) == 0:
            raise DagsterInvalidInvocationError(
                f"Decorated function '{compute_fn.name}' has context argument, but"
                " no context was provided when invoking."
            )
        if len(args) > 0:
            if args[0] is not None and not isinstance(args[0], BaseDirectExecutionContext):
                raise DagsterInvalidInvocationError(
                    f"Decorated function '{compute_fn.name}' has context argument, "
                    "but no context was provided when invoking."
                )
            context = args[0]
            # update args to omit context
            args = args[1:]
        else:  # context argument is provided under kwargs
            context_param_name = get_function_params(compute_fn.decorated_fn)[0].name
            if context_param_name not in kwargs:
                raise DagsterInvalidInvocationError(
                    f"Decorated function '{compute_fn.name}' has context argument "
                    f"'{context_param_name}', but no value for '{context_param_name}' was "
                    f"found when invoking. Provided kwargs: {kwargs}"
                )
            context = kwargs[context_param_name]
            # update kwargs to remove context
            kwargs = {
                kwarg: val for kwarg, val in kwargs.items() if not kwarg == context_param_name
            }
    # allow passing context, even if the function doesn't have an arg for it
    elif len(args) > 0 and isinstance(args[0], BaseDirectExecutionContext):
        context = args[0]
        args = args[1:]

    resource_arg_mapping = {arg.name: arg.name for arg in compute_fn.get_resource_args()}

    # The user is allowed to invoke an op with an arbitrary mix of args and kwargs.
    # We ensure that these args and kwargs are correctly categorized as inputs, config, or resource objects and then validated.
    #
    # Depending on arg/kwarg type, we do various things:
    # - Any resources passed as parameters are also made available to user-defined code as part of the op execution context
    # - Provide high-quality error messages (e.g. if something tried to pass a value to an input typed Nothing)
    # - Default values are applied appropriately
    # - Inputs are type checked
    #
    # We recollect all the varying args/kwargs into a dictionary and invoke the user-defined function with kwargs only.
    extracted = _separate_args_and_kwargs(compute_fn, args, kwargs, resource_arg_mapping)

    input_args = extracted.input_args
    input_kwargs = extracted.input_kwargs
    resources_by_param_name = extracted.resources_by_param_name
    config_input = extracted.config_arg

    bound_context = (context or build_op_context()).bind(
        op_def=op_def,
        pending_invocation=pending_invocation,
        assets_def=assets_def,
        resources_from_args=resources_by_param_name,
        config_from_args=(
            config_input._convert_to_config_dictionary()  # noqa: SLF001
            if isinstance(config_input, Config)
            else config_input
        ),
    )

    try:
        # if the compute function fails, we want to ensure we unbind the context. This
        # try-except handles "vanilla" asset and op invocation (generators and async handled in
        # _type_check_output_wrapper)

        input_dict = _resolve_inputs(op_def, input_args, input_kwargs, bound_context)  # type: ignore # (pyright bug)

        result = invoke_compute_fn(
            fn=compute_fn.decorated_fn,
            context=bound_context,  # type: ignore # (pyright bug)
            kwargs=input_dict,
            context_arg_provided=compute_fn.has_context_arg(),
            config_arg_cls=(
                compute_fn.get_config_arg().annotation if compute_fn.has_config_arg() else None
            ),
            resource_args=resource_arg_mapping,
        )
        return _type_check_output_wrapper(op_def, result, bound_context)  # type: ignore # (pyright bug)
    except Exception:
        bound_context.unbind()  # type: ignore # (pyright bug)
        raise


def _resolve_inputs(
    op_def: "OpDefinition", args, kwargs, context: "BaseDirectExecutionContext"
) -> Mapping[str, Any]:
    from dagster._core.execution.plan.execute_step import do_type_check

    nothing_input_defs = [
        input_def for input_def in op_def.input_defs if input_def.dagster_type.is_nothing
    ]

    # Check kwargs for nothing inputs, and error if someone provided one.
    for input_def in nothing_input_defs:
        if input_def.name in kwargs:
            node_label = op_def.node_type_str

            raise DagsterInvalidInvocationError(
                f"Attempted to provide value for nothing input '{input_def.name}'. Nothing "
                f"dependencies are ignored when directly invoking {node_label}s."
            )

    # Discard nothing dependencies - we ignore them during invocation.
    input_defs_by_name = {
        input_def.name: input_def
        for input_def in op_def.input_defs
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

        node_label = op_def.node_type_str
        raise DagsterInvalidInvocationError(
            f"Too many input arguments were provided for {node_label} '{context.per_invocation_properties.alias}'."
            f" {suggestion}"
        )

    # If more args were provided than the function has positional args, then fail early.
    positional_inputs = cast("DecoratedOpFunction", op_def.compute_fn).positional_inputs()
    if len(args) > len(positional_inputs):
        raise DagsterInvalidInvocationError(
            f"{op_def.node_type_str} '{op_def.name}' has {len(positional_inputs)} positional"
            f" inputs, but {len(args)} positional inputs were provided."
        )

    input_dict = {}

    for position, value in enumerate(args):
        input_name = positional_inputs[position]
        input_dict[input_name] = value
        # check for args/kwargs collisions
        if input_name in kwargs:
            raise DagsterInvalidInvocationError(
                f"{op_def.node_type_str} {op_def.name} got multiple values for argument"
                f" '{input_name}'"
            )

    for input_name in positional_inputs[len(args) :]:
        input_def = input_defs_by_name[input_name]

        if input_name in kwargs:
            input_dict[input_name] = kwargs[input_name]
        elif input_def.has_default_value:
            input_dict[input_name] = input_def.default_value
        else:
            raise DagsterInvalidInvocationError(
                f'No value provided for required input "{input_name}".'
            )

    unassigned_kwargs = {k: v for k, v in kwargs.items() if k not in input_dict}
    # If there are unassigned inputs, then they may be intended for use with a variadic keyword argument.
    if unassigned_kwargs and cast("DecoratedOpFunction", op_def.compute_fn).has_var_kwargs():
        input_dict.update(unassigned_kwargs)

    # Type check inputs
    op_label = context.per_invocation_properties.step_description

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
                metadata=type_check.metadata,
                dagster_type=dagster_type,
            )

    return input_dict


def _key_for_result(result: AssetResult, context: "BaseDirectExecutionContext") -> AssetKey:
    if not context.per_invocation_properties.assets_def:
        raise DagsterInvariantViolationError(
            f"Op {context.per_invocation_properties.alias} does not have an assets definition."
        )
    if result.asset_key:
        return result.asset_key

    if (
        context.per_invocation_properties.assets_def
        and len(context.per_invocation_properties.assets_def.keys) == 1
    ):
        return next(iter(context.per_invocation_properties.assets_def.keys))

    raise DagsterInvariantViolationError(
        f"{result.__class__.__name__} did not include asset_key and it can not be inferred. Specify which"
        f" asset_key, options are: {context.per_invocation_properties.assets_def.keys}"
    )


def _output_name_for_result_obj(
    event: Union[AssetResult, AssetCheckResult],
    context: "BaseDirectExecutionContext",
):
    if not context.per_invocation_properties.assets_def:
        raise DagsterInvariantViolationError(
            f"Op {context.per_invocation_properties.alias} does not have an assets definition."
        )

    if isinstance(event, AssetResult):
        asset_key = _key_for_result(event, context)
        return context.per_invocation_properties.assets_def.get_output_name_for_asset_key(asset_key)
    elif isinstance(event, AssetCheckResult):
        check_names_by_asset_key = {}
        for spec in context.per_invocation_properties.assets_def.check_specs:
            if spec.asset_key not in check_names_by_asset_key:
                check_names_by_asset_key[spec.asset_key] = []
            check_names_by_asset_key[spec.asset_key].append(spec.name)

        return context.per_invocation_properties.assets_def.get_output_name_for_asset_check_key(
            event.resolve_target_check_key(check_names_by_asset_key)
        )


def _handle_gen_event(
    event: T,
    op_def: "OpDefinition",
    context: "BaseDirectExecutionContext",
    output_defs: Mapping[str, OutputDefinition],
    outputs_seen: set[str],
) -> T:
    if isinstance(
        event,
        (AssetMaterialization, AssetObservation, ExpectationResult),
    ):
        return event
    elif isinstance(event, (AssetResult, AssetCheckResult)):
        output_name = _output_name_for_result_obj(event, context)
        outputs_seen.add(output_name)
        return event
    else:
        if not isinstance(event, (Output, DynamicOutput)):
            raise DagsterInvariantViolationError(
                f"When yielding outputs from a {op_def.node_type_str} generator,"
                " they should be wrapped in an `Output` object."
            )
        else:
            output_def = output_defs[event.output_name]
            _type_check_output(output_def, event, context)
            if output_def.name in outputs_seen and not isinstance(
                output_def, DynamicOutputDefinition
            ):
                raise DagsterInvariantViolationError(
                    f"Invocation of {op_def.node_type_str} '{context.per_invocation_properties.alias}' yielded"
                    f" an output '{output_def.name}' multiple times."
                )
            outputs_seen.add(output_def.name)
        return event


def _type_check_output_wrapper(
    op_def: "OpDefinition", result: Any, context: "BaseDirectExecutionContext"
) -> Any:
    """Type checks and returns the result of a op.

    If the op result is itself a generator, then wrap in a fxn that will type check and yield
    outputs.
    """
    output_defs = {output_def.name: output_def for output_def in op_def.output_defs}

    # Async generator case
    if inspect.isasyncgen(result):

        async def to_gen(async_gen):
            outputs_seen = set()

            try:
                # if the compute function fails, we want to ensure we unbind the context. For
                # async generators, the errors will only be surfaced here
                async for event in async_gen:
                    yield _handle_gen_event(event, op_def, context, output_defs, outputs_seen)
            except Exception:
                context.unbind()
                raise

            for output_def in op_def.output_defs:
                if (
                    output_def.name not in outputs_seen
                    and output_def.is_required
                    and not output_def.is_dynamic
                ):
                    # We require explicitly returned/yielded for asset observations
                    assets_def = context.per_invocation_properties.assets_def
                    is_observable_asset = assets_def is not None and assets_def.is_observable

                    if output_def.dagster_type.is_nothing and not is_observable_asset:
                        # implicitly yield None as we do in execute_step
                        yield Output(output_name=output_def.name, value=None)
                    else:
                        raise DagsterInvariantViolationError(
                            f"Invocation of {op_def.node_type_str} '{context.per_invocation_properties.alias}' did not"
                            f" return an output for non-optional output '{output_def.name}'"
                        )
            context.unbind()

        return to_gen(result)

    # Coroutine result case
    elif inspect.iscoroutine(result):

        async def type_check_coroutine(coro):
            try:
                # if the compute function fails, we want to ensure we unbind the context. For
                # async, the errors will only be surfaced here
                out = await coro
            except Exception:
                context.unbind()
                raise
            return _type_check_function_output(op_def, out, context)

        return type_check_coroutine(result)

    # Regular generator case
    elif inspect.isgenerator(result):

        def type_check_gen(gen):
            outputs_seen = set()
            try:
                # if the compute function fails, we want to ensure we unbind the context. For
                # generators, the errors will only be surfaced here
                for event in gen:
                    yield _handle_gen_event(event, op_def, context, output_defs, outputs_seen)
            except Exception:
                context.unbind()
                raise

            for output_def in op_def.output_defs:
                if (
                    output_def.name not in outputs_seen
                    and output_def.is_required
                    and not output_def.is_dynamic
                ):
                    # We require explicitly returned/yielded for asset observations
                    assets_def = context.per_invocation_properties.assets_def
                    is_observable_asset = assets_def is not None and assets_def.is_observable

                    if output_def.dagster_type.is_nothing and not is_observable_asset:
                        # implicitly yield None as we do in execute_step
                        yield Output(output_name=output_def.name, value=None)
                    else:
                        raise DagsterInvariantViolationError(
                            f'Invocation of {op_def.node_type_str} "{context.per_invocation_properties.alias}" did not'
                            f' return an output for non-optional output "{output_def.name}"'
                        )
            context.unbind()

        return type_check_gen(result)

    # Non-generator case
    return _type_check_function_output(op_def, result, context)


def _type_check_function_output(
    op_def: "OpDefinition", result: T, context: "BaseDirectExecutionContext"
) -> T:
    from dagster._core.execution.plan.compute_generator import (
        validate_and_coerce_op_result_to_iterator,
    )

    output_defs_by_name = {output_def.name: output_def for output_def in op_def.output_defs}
    op_context = _get_op_context(context)
    for event in validate_and_coerce_op_result_to_iterator(result, op_context, op_def.output_defs):
        if isinstance(event, (Output, DynamicOutput)):
            _type_check_output(output_defs_by_name[event.output_name], event, context)
        elif isinstance(event, AssetResult):
            # ensure result objects are contextually valid
            _output_name_for_result_obj(event, context)

    context.unbind()
    return result


def _type_check_output(
    output_def: "OutputDefinition",
    output: Union[Output, DynamicOutput],
    context: "BaseDirectExecutionContext",
) -> None:
    """Validates and performs core type check on a provided output.

    Args:
        output_def (OutputDefinition): The output definition to validate against.
        output (Any): The output to validate.
        context (BaseDirectExecutionContext): Context containing resources to be used for type
            check.
    """
    from dagster._core.execution.plan.execute_step import do_type_check

    op_label = context.per_invocation_properties.step_description
    dagster_type = output_def.dagster_type
    type_check = do_type_check(context.for_type(dagster_type), dagster_type, output.value)
    if not type_check.success:
        raise DagsterTypeCheckDidNotPass(
            description=(
                f'Type check failed for {op_label} output "{output.output_name}" - '
                f'expected type "{dagster_type.display_name}". '
                f"Description: {type_check.description}"
            ),
            metadata=type_check.metadata,
            dagster_type=dagster_type,
        )

    context.observe_output(
        output_def.name, output.mapping_key if isinstance(output, DynamicOutput) else None
    )
