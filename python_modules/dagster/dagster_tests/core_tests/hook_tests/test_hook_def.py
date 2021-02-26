from collections import defaultdict

import pytest
from dagster import (
    DagsterEventType,
    ModeDefinition,
    PipelineDefinition,
    SolidInvocation,
    execute_pipeline,
    pipeline,
    reconstructable,
    resource,
    solid,
)
from dagster.core.definitions import failure_hook, success_hook
from dagster.core.definitions.decorators.hook import event_list_hook
from dagster.core.definitions.events import HookExecutionResult
from dagster.core.errors import DagsterInvalidDefinitionError


class SomeUserException(Exception):
    pass


@resource
def resource_a(_init_context):
    return 1


def test_hook():
    called = {}

    @event_list_hook
    def a_hook(context, event_list):
        called[context.hook_def.name] = context.solid.name
        called["step_event_list"] = [i for i in event_list]
        return HookExecutionResult(hook_name="a_hook")

    @event_list_hook(name="a_named_hook")
    def named_hook(context, _):
        called[context.hook_def.name] = context.solid.name
        return HookExecutionResult(hook_name="a_hook")

    @solid
    def a_solid(_):
        pass

    a_pipeline = PipelineDefinition(
        solid_defs=[a_solid],
        dependencies={
            SolidInvocation("a_solid", "a_solid_with_hook", hook_defs={a_hook, named_hook}): {}
        },
    )

    result = execute_pipeline(a_pipeline)
    assert result.success
    assert called.get("a_hook") == "a_solid_with_hook"
    assert called.get("a_named_hook") == "a_solid_with_hook"

    assert set([event.event_type_value for event in called["step_event_list"]]) == set(
        [event.event_type_value for event in result.step_event_list]
    )


def test_hook_user_error():
    @event_list_hook
    def error_hook(context, _):
        raise SomeUserException()

    @solid
    def a_solid(_):
        return 1

    a_pipeline = PipelineDefinition(
        solid_defs=[a_solid],
        dependencies={SolidInvocation("a_solid", "a_solid_with_hook", hook_defs={error_hook}): {}},
    )

    result = execute_pipeline(a_pipeline)
    assert result.success

    hook_errored_events = list(
        filter(lambda event: event.event_type == DagsterEventType.HOOK_ERRORED, result.event_list)
    )
    assert len(hook_errored_events) == 1
    assert hook_errored_events[0].solid_handle.name == "a_solid_with_hook"


def test_hook_decorator_arg_error():
    with pytest.raises(DagsterInvalidDefinitionError, match="does not have required positional"):

        @success_hook
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match="does not have required positional"):

        @failure_hook
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match="does not have required positional"):

        @event_list_hook()
        def _(_):
            pass


def test_hook_with_resource():
    called = {}

    @event_list_hook(required_resource_keys={"resource_a"})
    def a_hook(context, _):
        called[context.solid.name] = True
        assert context.resources.resource_a == 1
        return HookExecutionResult(hook_name="a_hook")

    @solid
    def a_solid(_):
        pass

    a_pipeline = PipelineDefinition(
        solid_defs=[a_solid],
        dependencies={SolidInvocation("a_solid", "a_solid_with_hook", hook_defs={a_hook}): {}},
        mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})],
    )

    result = execute_pipeline(a_pipeline)
    assert result.success
    assert called.get("a_solid_with_hook")


def test_hook_resource_error():
    @event_list_hook(required_resource_keys={"resource_b"})
    def a_hook(context, event_list):  # pylint: disable=unused-argument
        return HookExecutionResult(hook_name="a_hook")

    @solid
    def a_solid(_):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='Resource "resource_b" is required by hook "a_hook"'
    ):
        PipelineDefinition(
            solid_defs=[a_solid],
            dependencies={SolidInvocation("a_solid", "a_solid_with_hook", hook_defs={a_hook}): {}},
            mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})],
        )


def test_success_hook():

    called_hook_to_solids = defaultdict(list)

    @success_hook
    def a_success_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)

    @success_hook(name="a_named_success_hook")
    def named_success_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)

    @success_hook(required_resource_keys={"resource_a"})
    def success_hook_resource(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def succeeded_solid(_):
        pass

    @solid
    def failed_solid(_):
        # this solid shouldn't trigger success hooks
        raise SomeUserException()

    a_pipeline = PipelineDefinition(
        solid_defs=[succeeded_solid, failed_solid],
        dependencies={
            SolidInvocation(
                "succeeded_solid",
                "succeeded_solid_with_hook",
                hook_defs={a_success_hook, named_success_hook, success_hook_resource},
            ): {},
            SolidInvocation(
                "failed_solid",
                "failed_solid_with_hook",
                hook_defs={a_success_hook, named_success_hook},
            ): {},
        },
        mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})],
    )

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success

    # test if hooks are run for the given solids
    assert "succeeded_solid_with_hook" in called_hook_to_solids["a_success_hook"]
    assert "succeeded_solid_with_hook" in called_hook_to_solids["a_named_success_hook"]
    assert "succeeded_solid_with_hook" in called_hook_to_solids["success_hook_resource"]
    assert "failed_solid_with_hook" not in called_hook_to_solids["a_success_hook"]
    assert "failed_solid_with_hook" not in called_hook_to_solids["a_named_success_hook"]


def test_failure_hook():

    called_hook_to_solids = defaultdict(list)

    @failure_hook
    def a_failure_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)

    @failure_hook(name="a_named_failure_hook")
    def named_failure_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)

    @failure_hook(required_resource_keys={"resource_a"})
    def failure_hook_resource(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def succeeded_solid(_):
        # this solid shouldn't trigger failure hooks
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    a_pipeline = PipelineDefinition(
        solid_defs=[failed_solid, succeeded_solid],
        dependencies={
            SolidInvocation(
                "failed_solid",
                "failed_solid_with_hook",
                hook_defs={a_failure_hook, named_failure_hook, failure_hook_resource},
            ): {},
            SolidInvocation(
                "succeeded_solid",
                "succeeded_solid_with_hook",
                hook_defs={a_failure_hook, named_failure_hook},
            ): {},
        },
        mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})],
    )

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    # test if hooks are run for the given solids
    assert "failed_solid_with_hook" in called_hook_to_solids["a_failure_hook"]
    assert "failed_solid_with_hook" in called_hook_to_solids["a_named_failure_hook"]
    assert "failed_solid_with_hook" in called_hook_to_solids["failure_hook_resource"]
    assert "succeeded_solid_with_hook" not in called_hook_to_solids["a_failure_hook"]
    assert "succeeded_solid_with_hook" not in called_hook_to_solids["a_named_failure_hook"]


def test_success_hook_event():
    @success_hook
    def a_hook(_):
        pass

    @solid
    def a_solid(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    a_pipeline = PipelineDefinition(
        solid_defs=[a_solid, failed_solid],
        dependencies={
            SolidInvocation("a_solid", hook_defs={a_hook}): {},
            SolidInvocation("failed_solid", hook_defs={a_hook}): {},
        },
    )

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success

    hook_events = list(filter(lambda event: event.is_hook_event, result.event_list))
    # when a hook is not triggered, we fire hook skipped event instead of completed
    assert len(hook_events) == 2
    for event in hook_events:
        if event.event_type == DagsterEventType.HOOK_COMPLETED:
            assert event.solid_name == "a_solid"
        if event.event_type == DagsterEventType.HOOK_SKIPPED:
            assert event.solid_name == "failed_solid"


def test_failure_hook_event():
    @failure_hook
    def a_hook(_):
        pass

    @solid
    def a_solid(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    a_pipeline = PipelineDefinition(
        solid_defs=[a_solid, failed_solid],
        dependencies={
            SolidInvocation("a_solid", hook_defs={a_hook}): {},
            SolidInvocation("failed_solid", hook_defs={a_hook}): {},
        },
    )

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success

    hook_events = list(filter(lambda event: event.is_hook_event, result.event_list))
    # when a hook is not triggered, we fire hook skipped event instead of completed
    assert len(hook_events) == 2
    for event in hook_events:
        if event.event_type == DagsterEventType.HOOK_COMPLETED:
            assert event.solid_name == "failed_solid"
        if event.event_type == DagsterEventType.HOOK_SKIPPED:
            assert event.solid_name == "a_solid"


@solid
def noop(_):
    return


@success_hook
def noop_hook(_):
    return


@noop_hook
@pipeline
def foo():
    noop()


def test_pipelines_with_hooks_are_reconstructable():
    assert reconstructable(foo)
