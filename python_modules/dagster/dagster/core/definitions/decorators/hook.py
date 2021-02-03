from functools import update_wrapper

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from ...decorator_utils import split_function_parameters, validate_decorated_fn_positionals
from ..events import HookExecutionResult
from ..hook import HookDefinition


class _Hook:
    def __init__(self, name=None, required_resource_keys=None):
        self.name = check.opt_str_param(name, "name")
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        expected_positionals = ["context", "event_list"]
        fn_positionals, _ = split_function_parameters(fn, expected_positionals)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, expected_positionals)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "'{hook_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. Hook functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context' and "
                "a second positional parameter named 'event_list'.".format(
                    hook_name=fn.__name__, missing_param=missing_positional
                )
            )

        hook_def = HookDefinition(
            name=self.name,
            hook_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )
        update_wrapper(hook_def, fn)
        return hook_def


def event_list_hook(name=None, required_resource_keys=None):
    """Create a generic hook with the specified parameters from the decorated function.

    This decorator is currently used internally by Dagster machinery to support success_hook and
    failure_hook.

    The user-defined hook function requires two parameters:
    - A `context` object is passed as the first parameter. The context is an instance of
        :py:class:`context <HookContext>`, and provides access to system
        information, such as loggers (context.log), resources (context.resources), the solid
        (context.solid) and its execution step (context.step) which triggers this hook.
    - An `event_list` object is passed as the second paramter. It provides the full event list of the
        associated execution step.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            hook.

    Examples:

        .. code-block:: python

            @event_list_hook(required_resource_keys={'slack'})
            def slack_on_materializations(context, event_list):
                for event in event_list:
                    if event.event_type == DagsterEventType.STEP_MATERIALIZATION:
                        message = '{solid} has materialized an asset {key}.'.format(
                            solid=context.solid.name,
                            key=event.asset_key
                        )
                        # send a slack message every time a materialization event occurs
                        context.resources.slack.send_message(message)


    """
    # This case is for when decorator is used bare, without arguments.
    # e.g. @event_list_hook versus @event_list_hook()
    if callable(name):
        check.invariant(required_resource_keys is None)
        return _Hook()(name)

    return _Hook(name=name, required_resource_keys=required_resource_keys)


def success_hook(name=None, required_resource_keys=None):
    """Create a hook on step success events with the specified parameters from the decorated function.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            hook.

    Examples:

        .. code-block:: python

            @success_hook(required_resource_keys={'slack'})
            def slack_message_on_success(context):
                message = 'solid {} succeeded'.format(context.solid.name)
                context.resources.slack.send_message(message)

            @success_hook
            def do_something_on_success(context):
                do_something()


    """

    def wrapper(fn):
        check.callable_param(fn, "fn")

        expected_positionals = ["context"]
        fn_positionals, _ = split_function_parameters(fn, expected_positionals)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, expected_positionals)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@success_hook '{hook_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. Hook functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    hook_name=fn.__name__, missing_param=missing_positional
                )
            )

        if name is None or callable(name):
            _name = fn.__name__
        else:
            _name = name

        @event_list_hook(_name, required_resource_keys)
        def _success_hook(context, event_list):
            for event in event_list:
                if event.is_step_success:
                    fn(context)
                    return HookExecutionResult(hook_name=_name, is_skipped=False)

            # hook is skipped when fn didn't run
            return HookExecutionResult(hook_name=_name, is_skipped=True)

        return _success_hook

    # This case is for when decorator is used bare, without arguments, i.e. @success_hook
    if callable(name):
        check.invariant(required_resource_keys is None)
        return wrapper(name)

    return wrapper


def failure_hook(name=None, required_resource_keys=None):
    """Create a hook on step failure events with the specified parameters from the decorated function.

    Args:
        name (Optional[str]): The name of this hook.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            hook.

    Examples:

        .. code-block:: python

            @failure_hook(required_resource_keys={'slack'})
            def slack_message_on_failure(context):
                message = 'solid {} failed'.format(context.solid.name)
                context.resources.slack.send_message(message)

            @failure_hook
            def do_something_on_failure(context):
                do_something()


    """

    def wrapper(fn):
        check.callable_param(fn, "fn")

        expected_positionals = ["context"]
        fn_positionals, _ = split_function_parameters(fn, expected_positionals)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, expected_positionals)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@failure_hook '{hook_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. Hook functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    hook_name=fn.__name__, missing_param=missing_positional
                )
            )

        if name is None or callable(name):
            _name = fn.__name__
        else:
            _name = name

        @event_list_hook(_name, required_resource_keys)
        def _failure_hook(context, event_list):
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
