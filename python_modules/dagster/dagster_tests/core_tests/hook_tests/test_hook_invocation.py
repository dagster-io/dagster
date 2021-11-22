import re

import mock
import pytest
from dagster import HookContext, build_hook_context, failure_hook, resource, solid, success_hook
from dagster.core.definitions.decorators.hook import event_list_hook
from dagster.core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError


def test_event_list_hook_invocation():
    entered = []

    @event_list_hook
    def basic_event_list_hook(context, event_list):
        assert isinstance(context, HookContext)
        for event in event_list:
            if event.is_step_success:
                entered.append("yes")

    basic_event_list_hook(build_hook_context(), [mock.MagicMock(is_step_success=True)])
    assert entered == ["yes"]
    entered = []

    basic_event_list_hook(build_hook_context(), event_list=[mock.MagicMock(is_step_success=True)])
    assert entered == ["yes"]

    entered = []

    basic_event_list_hook(
        context=build_hook_context(), event_list=[mock.MagicMock(is_step_success=True)]
    )
    assert entered == ["yes"]

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Decorated function expects two parameters, context and event_list, but 0 were provided.",
    ):
        basic_event_list_hook()  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Decorated function expects two parameters, context and event_list, but 1 were provided.",
    ):
        basic_event_list_hook(event_list=[])  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Decorated function expects two parameters, context and event_list, but 1 were provided.",
    ):
        basic_event_list_hook(context=None)  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Decorated function expects two parameters, context and event_list, but 1 were provided.",
    ):
        basic_event_list_hook(None)  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError, match="Could not find expected argument 'context'."
    ):
        basic_event_list_hook(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            foo=None, event_list=[]
        )

    with pytest.raises(
        DagsterInvalidInvocationError, match="Could not find expected argument 'event_list'."
    ):
        basic_event_list_hook(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            context=None, bar=[]
        )


@pytest.mark.parametrize("hook_decorator", [success_hook, failure_hook])
def test_context_hook_invocation(hook_decorator):
    entered = []

    @hook_decorator
    def my_hook(_):
        entered.append("yes")

    my_hook(None)
    assert entered == ["yes"]

    entered = []
    my_hook(build_hook_context())
    assert entered == ["yes"]

    entered = []
    my_hook(_=build_hook_context())
    assert entered == ["yes"]

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Decorated function expects one parameter, _, but 0 were provided.",
    ):
        my_hook()  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError, match="Could not find expected argument '_'."
    ):
        my_hook(foo=None)  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter


@pytest.mark.parametrize(
    "hook_decorator,is_event_list_hook",
    [(success_hook, False), (failure_hook, False), (event_list_hook, True)],
)
def test_success_hook_with_resources(hook_decorator, is_event_list_hook):

    decorator = hook_decorator(required_resource_keys={"foo", "bar"})
    if is_event_list_hook:

        def my_hook_reqs_resources(context, _):
            assert context.resources.foo == "foo"
            assert context.resources.bar == "bar"

        hook = decorator(my_hook_reqs_resources)
    else:

        def my_hook_reqs_resources(context):  # type: ignore[misc]
            assert context.resources.foo == "foo"
            assert context.resources.bar == "bar"

        hook = decorator(my_hook_reqs_resources)

    @resource
    def bar_resource(_):
        return "bar"

    if is_event_list_hook:
        hook(build_hook_context(resources={"foo": "foo", "bar": bar_resource}), None)
    else:
        hook(build_hook_context(resources={"foo": "foo", "bar": bar_resource}))

    with pytest.raises(
        DagsterInvariantViolationError,
        match=r"The hook 'my_hook_reqs_resources' requires resource '\w+', "
        r"which was not provided by the context.",
    ):
        if is_event_list_hook:
            hook(None, None)
        else:
            hook(None)


@pytest.mark.parametrize(
    "hook_decorator,is_event_list_hook",
    [(success_hook, False), (failure_hook, False), (event_list_hook, True)],
)
def test_success_hook_cm_resource(hook_decorator, is_event_list_hook):
    entered = []

    @resource
    def cm_resource(_):
        try:
            entered.append("try")
            yield "foo"
        finally:
            entered.append("finally")

    decorator = hook_decorator(required_resource_keys={"cm"})
    if is_event_list_hook:

        def my_hook_cm_resource(context, _):
            assert context.resources.cm == "foo"
            assert entered == ["try"]

        hook = decorator(my_hook_cm_resource)
    else:

        def my_hook_cm_resource(context):  # type: ignore[misc]
            assert context.resources.cm == "foo"
            assert entered == ["try"]

        hook = decorator(my_hook_cm_resource)

    with build_hook_context(resources={"cm": cm_resource}) as context:
        if is_event_list_hook:
            hook(context, None)
        else:
            hook(context)

    assert entered == ["try", "finally"]

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "At least one provided resource is a generator, but attempting to access resources "
            "outside of context manager scope. You can use the following syntax to open a context "
            "manager: `with build_hook_context(...) as context:`"
        ),
    ):
        if is_event_list_hook:
            hook(build_hook_context(resources={"cm": cm_resource}), None)
        else:
            hook(build_hook_context(resources={"cm": cm_resource}))


def test_hook_invocation_with_solid():
    @success_hook
    def basic_hook(context):
        assert context.solid.name == "foo"
        assert len(context.solid.graph_definition.solids) == 1

    @solid
    def foo():
        pass

    @solid
    def not_foo():
        pass

    basic_hook(build_hook_context(solid=foo))
    basic_hook(build_hook_context(solid=not_foo.alias("foo")))


def test_properties_on_hook_context():
    @success_hook
    def basic_hook(context):
        assert isinstance(context.job_name, str)
        assert isinstance(context.run_id, str)
        assert isinstance(context.op_exception, BaseException)

    error = DagsterInvariantViolationError("blah")
    basic_hook(build_hook_context(run_id="blah", job_name="blah", op_exception=error))
