from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Optional,
    Sequence,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError

from ...decorator_utils import get_function_params, validate_expected_params
from ..events import HookExecutionResult
from ..hook_definition import HookDefinition

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.hook import HookContext


def _validate_hook_fn_params(fn, expected_positionals):
    params = get_function_params(fn)
    missing_positional = validate_expected_params(params, expected_positionals)
    if missing_positional:
        raise DagsterInvalidDefinitionError(
            f"'{fn.__name__}' decorated function does not have required positional "
            f"parameter '{missing_positional}'. Hook functions should only have keyword arguments "
            "that match input names and a first positional parameter named 'context' and "
            "a second positional parameter named 'event_list'."
        )


class _Hook:
    def __init__(
        self,
        name: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        decorated_fn: Optional[Callable[..., Any]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )
        self.decorated_fn = check.opt_callable_param(decorated_fn, "decorated_fn")

    def __call__(self, fn) -> HookDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        expected_positionals = ["context", "event_list"]

        _validate_hook_fn_params(fn, expected_positionals)

        hook_def = HookDefinition(
            name=self.name or "",
            hook_fn=fn,
            required_resource_keys=self.required_resource_keys,
            decorated_fn=self.decorated_fn or fn,
        )
        update_wrapper(cast(Callable[..., Any], hook_def), fn)
        return hook_def


@overload
def event_list_hook(
    hook_fn: Callable,
) -> HookDefinition:
    pass


@overload
def event_list_hook(
    *,
    name: Optional[str] = ...,
    required_resource_keys: Optional[AbstractSet[str]] = ...,
    decorated_fn: Optional[Callable[..., Any]] = ...,
) -> _Hook:
    pass


def event_list_hook(
    hook_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    decorated_fn: Optional[Callable[..., Any]] = None,
) -> Union[HookDefinition, _Hook]:
    """Create a generic hook with the specified parameters from the decorated function.

    This decorator is currently used internally by Dagster machinery to support success_hook and
    failure_hook.

    The user-defined hook function requires two parameters:
    - A `context` object is passed as the first parameter. The context is an instance of
        :py:class:`context <HookContext>`, and provides access to system
        information, such as loggers (context.log), resources (context.resources), the op
        (context.op) and its execution step (context.step) which triggers this hook.
    - An `event_list` object is passed as the second paramter. It provides the full event list of the
        associated execution step.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[AbstractSet[str]]): Keys for the resources required by the
            hook.

    Examples:
        .. code-block:: python

            @event_list_hook(required_resource_keys={'slack'})
            def slack_on_materializations(context, event_list):
                for event in event_list:
                    if event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
                        message = f'{context.op_name} has materialized an asset {event.asset_key}.'
                        # send a slack message every time a materialization event occurs
                        context.resources.slack.send_message(message)


    """
    # This case is for when decorator is used bare, without arguments.
    # e.g. @event_list_hook versus @event_list_hook()
    if hook_fn is not None:
        check.invariant(required_resource_keys is None)
        return _Hook()(hook_fn)

    return _Hook(
        name=name, required_resource_keys=required_resource_keys, decorated_fn=decorated_fn
    )


SuccessOrFailureHookFn = Callable[["HookContext"], Any]


@overload
def success_hook(hook_fn: SuccessOrFailureHookFn) -> HookDefinition: ...


@overload
def success_hook(
    *,
    name: Optional[str] = ...,
    required_resource_keys: Optional[AbstractSet[str]] = ...,
) -> Callable[[SuccessOrFailureHookFn], HookDefinition]: ...


def success_hook(
    hook_fn: Optional[SuccessOrFailureHookFn] = None,
    *,
    name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
) -> Union[HookDefinition, Callable[[SuccessOrFailureHookFn], HookDefinition]]:
    """Create a hook on step success events with the specified parameters from the decorated function.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[AbstractSet[str]]): Keys for the resources required by the
            hook.

    Examples:
        .. code-block:: python

            @success_hook(required_resource_keys={'slack'})
            def slack_message_on_success(context):
                message = 'op {} succeeded'.format(context.op.name)
                context.resources.slack.send_message(message)

            @success_hook
            def do_something_on_success(context):
                do_something()


    """

    def wrapper(fn: SuccessOrFailureHookFn) -> HookDefinition:
        check.callable_param(fn, "fn")

        expected_positionals = ["context"]
        _validate_hook_fn_params(fn, expected_positionals)

        if name is None or callable(name):
            _name = fn.__name__
        else:
            _name = name

        @event_list_hook(name=_name, required_resource_keys=required_resource_keys, decorated_fn=fn)
        def _success_hook(
            context: "HookContext", event_list: Sequence["DagsterEvent"]
        ) -> HookExecutionResult:
            for event in event_list:
                if event.is_step_success:
                    fn(context)
                    return HookExecutionResult(hook_name=_name, is_skipped=False)

            # hook is skipped when fn didn't run
            return HookExecutionResult(hook_name=_name, is_skipped=True)

        return _success_hook

    # This case is for when decorator is used bare, without arguments, i.e. @success_hook
    if hook_fn is not None:
        check.invariant(required_resource_keys is None)
        return wrapper(hook_fn)

    return wrapper


@overload
def failure_hook(name: SuccessOrFailureHookFn) -> HookDefinition: ...


@overload
def failure_hook(
    name: Optional[str] = ...,
    required_resource_keys: Optional[AbstractSet[str]] = ...,
) -> Callable[[SuccessOrFailureHookFn], HookDefinition]: ...


def failure_hook(
    name: Optional[Union[SuccessOrFailureHookFn, str]] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
) -> Union[HookDefinition, Callable[[SuccessOrFailureHookFn], HookDefinition]]:
    """Create a hook on step failure events with the specified parameters from the decorated function.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[AbstractSet[str]]): Keys for the resources required by the
            hook.

    Examples:
        .. code-block:: python

            @failure_hook(required_resource_keys={'slack'})
            def slack_message_on_failure(context):
                message = 'op {} failed'.format(context.op.name)
                context.resources.slack.send_message(message)

            @failure_hook
            def do_something_on_failure(context):
                do_something()


    """

    def wrapper(fn: Callable[["HookContext"], Any]) -> HookDefinition:
        check.callable_param(fn, "fn")

        expected_positionals = ["context"]
        _validate_hook_fn_params(fn, expected_positionals)

        if name is None or callable(name):
            _name = fn.__name__
        else:
            _name = name

        @event_list_hook(name=_name, required_resource_keys=required_resource_keys, decorated_fn=fn)
        def _failure_hook(
            context: "HookContext", event_list: Sequence["DagsterEvent"]
        ) -> HookExecutionResult:
            for event in event_list:
                if event.is_step_failure:
                    fn(context)
                    return HookExecutionResult(hook_name=_name, is_skipped=False)

            # hook is skipped when fn didn't run
            return HookExecutionResult(hook_name=_name, is_skipped=True)

        return _failure_hook

    # This case is for when decorator is used bare, without arguments, i.e. @failure_hook
    if callable(name):
        check.invariant(required_resource_keys is None)
        return wrapper(name)

    return wrapper
