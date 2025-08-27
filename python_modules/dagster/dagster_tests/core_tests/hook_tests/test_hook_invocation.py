import re
from unittest import mock

import dagster as dg
import pytest
from dagster._core.definitions.decorators.hook_decorator import event_list_hook


def test_event_list_hook_invocation():
    entered = []

    @event_list_hook
    def basic_event_list_hook(context, event_list):
        assert isinstance(context, dg.HookContext)
        for event in event_list:
            if event.is_step_success:
                entered.append("yes")

    basic_event_list_hook(dg.build_hook_context(), [mock.MagicMock(is_step_success=True)])
    assert entered == ["yes"]
    entered = []

    basic_event_list_hook(
        dg.build_hook_context(), event_list=[mock.MagicMock(is_step_success=True)]
    )
    assert entered == ["yes"]

    entered = []

    basic_event_list_hook(
        context=dg.build_hook_context(), event_list=[mock.MagicMock(is_step_success=True)]
    )
    assert entered == ["yes"]

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function expects two parameters, context and event_list, but 0 were"
            " provided."
        ),
    ):
        basic_event_list_hook()

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function expects two parameters, context and event_list, but 1 were"
            " provided."
        ),
    ):
        basic_event_list_hook(event_list=[])

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function expects two parameters, context and event_list, but 1 were"
            " provided."
        ),
    ):
        basic_event_list_hook(context=None)

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function expects two parameters, context and event_list, but 1 were"
            " provided."
        ),
    ):
        basic_event_list_hook(None)

    with pytest.raises(
        dg.DagsterInvalidInvocationError, match="Could not find expected argument 'context'."
    ):
        basic_event_list_hook(foo=None, event_list=[])

    with pytest.raises(
        dg.DagsterInvalidInvocationError, match="Could not find expected argument 'event_list'."
    ):
        basic_event_list_hook(context=None, bar=[])


@pytest.mark.parametrize("hook_decorator", [dg.success_hook, dg.failure_hook])
def test_context_hook_invocation(hook_decorator):
    entered = []

    @hook_decorator
    def my_hook(_):
        entered.append("yes")

    my_hook(None)
    assert entered == ["yes"]

    entered = []
    my_hook(dg.build_hook_context())
    assert entered == ["yes"]

    entered = []
    my_hook(_=dg.build_hook_context())
    assert entered == ["yes"]

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Decorated function expects one parameter, _, but 0 were provided.",
    ):
        my_hook()  # pyright: ignore[reportCallIssue]

    with pytest.raises(
        dg.DagsterInvalidInvocationError, match="Could not find expected argument '_'."
    ):
        my_hook(foo=None)  # pyright: ignore[reportCallIssue]


@pytest.mark.parametrize(
    "hook_decorator,is_event_list_hook",
    [(dg.success_hook, False), (dg.failure_hook, False), (event_list_hook, True)],
)
def test_success_hook_with_resources(hook_decorator, is_event_list_hook):
    decorator = hook_decorator(required_resource_keys={"foo", "bar"})
    if is_event_list_hook:

        def my_hook_reqs_resources(context, _):  # type: ignore  # (test rename)
            assert context.resources.foo == "foo"
            assert context.resources.bar == "bar"

        hook = decorator(my_hook_reqs_resources)
    else:

        def my_hook_reqs_resources(context):
            assert context.resources.foo == "foo"
            assert context.resources.bar == "bar"

        hook = decorator(my_hook_reqs_resources)

    @dg.resource
    def bar_resource(_):
        return "bar"

    if is_event_list_hook:
        hook(dg.build_hook_context(resources={"foo": "foo", "bar": bar_resource}), None)
    else:
        hook(dg.build_hook_context(resources={"foo": "foo", "bar": bar_resource}))

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'bar' required by hook 'my_hook_reqs_resources'  was not provided",
    ):
        if is_event_list_hook:
            hook(None, None)
        else:
            hook(None)


@pytest.mark.parametrize(
    "hook_decorator,is_event_list_hook",
    [(dg.success_hook, False), (dg.failure_hook, False), (event_list_hook, True)],
)
def test_success_hook_cm_resource(hook_decorator, is_event_list_hook):
    entered = []

    @dg.resource
    def cm_resource(_):
        try:
            entered.append("try")
            yield "foo"
        finally:
            entered.append("finally")

    decorator = hook_decorator(required_resource_keys={"cm"})
    if is_event_list_hook:

        def my_hook_cm_resource_1(context, _):
            assert context.resources.cm == "foo"
            assert entered == ["try"]

        hook = decorator(my_hook_cm_resource_1)
    else:

        def my_hook_cm_resource_2(context):
            assert context.resources.cm == "foo"
            assert entered == ["try"]

        hook = decorator(my_hook_cm_resource_2)

    with dg.build_hook_context(resources={"cm": cm_resource}) as context:
        if is_event_list_hook:
            hook(context, None)
        else:
            hook(context)

    assert entered == ["try", "finally"]

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "At least one provided resource is a generator, but attempting to access resources "
            "outside of context manager scope. You can use the following syntax to open a context "
            "manager: `with build_hook_context(...) as context:`"
        ),
    ):
        if is_event_list_hook:
            hook(dg.build_hook_context(resources={"cm": cm_resource}), None)
        else:
            hook(dg.build_hook_context(resources={"cm": cm_resource}))


def test_hook_invocation_with_op():
    @dg.success_hook
    def basic_hook(context):
        assert context.op.name == "foo"
        assert len(context.op.graph_definition.nodes) == 1

    @dg.op
    def foo():
        pass

    @dg.op
    def not_foo():
        pass

    basic_hook(dg.build_hook_context(op=foo))
    basic_hook(dg.build_hook_context(op=not_foo.alias("foo")))


def test_properties_on_hook_context():
    @dg.success_hook
    def basic_hook(context):
        assert isinstance(context.job_name, str)
        assert isinstance(context.run_id, str)
        assert isinstance(context.op_exception, BaseException)
        assert isinstance(context.instance, dg.DagsterInstance)

    error = dg.DagsterInvariantViolationError("blah")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "Tried to access the HookContext instance, but no instance was provided to"
            " `build_hook_context`."
        ),
    ):
        basic_hook(dg.build_hook_context(run_id="blah", job_name="blah", op_exception=error))

    with dg.instance_for_test() as instance:
        basic_hook(
            dg.build_hook_context(
                run_id="blah", job_name="blah", op_exception=error, instance=instance
            )
        )
