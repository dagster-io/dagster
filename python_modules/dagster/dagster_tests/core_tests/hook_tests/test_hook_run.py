from collections import defaultdict

import pytest
from dagster import (
    Int,
    ModeDefinition,
    composite_solid,
    execute_pipeline,
    pipeline,
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


def test_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook(required_resource_keys={"resource_a"})
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1
        return HookExecutionResult("a_hook")

    @solid
    def a_solid(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        a_solid.with_hooks(hook_defs={a_hook})()
        a_solid.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        a_solid.alias("solid_without_hook")()

    result = execute_pipeline(a_pipeline)
    assert result.success
    assert called_hook_to_solids["a_hook"] == {"a_solid", "solid_with_hook"}


def test_hook_accumulation():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def pipeline_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step.key)
        return HookExecutionResult("pipeline_hook")

    @event_list_hook
    def solid_1_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step.key)
        return HookExecutionResult("solid_1_hook")

    @event_list_hook
    def composite_1_hook(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step.key)
        return HookExecutionResult("composite_1_hook")

    @solid
    def solid_1(_):
        return 1

    @solid
    def solid_2(_, num):
        return num

    @solid
    def solid_3(_):
        return 1

    @composite_solid
    def composite_1():
        return solid_2(solid_1.with_hooks({solid_1_hook})())

    @composite_solid
    def composite_2():
        solid_3()
        return composite_1.with_hooks({composite_1_hook})()

    @pipeline_hook
    @pipeline
    def a_pipeline():
        composite_2()

    result = execute_pipeline(a_pipeline)
    assert result.success

    # make sure we gather hooks from all places and invoke them with the right steps
    assert called_hook_to_step_keys == {
        "pipeline_hook": {
            "composite_2.composite_1.solid_1",
            "composite_2.composite_1.solid_2",
            "composite_2.solid_3",
        },
        "solid_1_hook": {"composite_2.composite_1.solid_1"},
        "composite_1_hook": {
            "composite_2.composite_1.solid_1",
            "composite_2.composite_1.solid_2",
        },
    }


def test_hook_on_composite_solid_instance():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step.key)
        return HookExecutionResult("hook_a_generic")

    @solid
    def two(_):
        return 1

    @solid
    def add_one(_, num):
        return num + 1

    @composite_solid
    def add_two():
        adder_1 = add_one.alias("adder_1")
        adder_2 = add_one.alias("adder_2")

        return adder_2(adder_1(two()))

    @pipeline
    def a_pipeline():
        add_two.with_hooks({hook_a_generic})()

    result = execute_pipeline(a_pipeline)
    assert result.success
    # the hook should run on all steps inside a composite
    assert called_hook_to_step_keys["hook_a_generic"] == set(
        [i.step_key for i in filter(lambda i: i.is_step_event, result.event_list)]
    )


def test_success_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @success_hook(required_resource_keys={"resource_a"})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def a_solid(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        a_solid.with_hooks(hook_defs={a_hook})()
        a_solid.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        a_solid.alias("solid_without_hook")()
        failed_solid.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids["a_hook"] == {"a_solid", "solid_with_hook"}


def test_failure_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @failure_hook(required_resource_keys={"resource_a"})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @solid
    def a_succeeded_solid(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"resource_a": resource_a})])
    def a_pipeline():
        failed_solid.with_hooks(hook_defs={a_hook})()
        failed_solid.alias("solid_with_hook").with_hooks(hook_defs={a_hook})()
        failed_solid.alias("solid_without_hook")()
        a_succeeded_solid.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids["a_hook"] == {"failed_solid", "solid_with_hook"}


def test_hook_on_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult("hook_a_generic")

    @event_list_hook
    def hook_b_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult("hook_b_generic")

    @solid
    def solid_a(_):
        pass

    @solid
    def solid_b(_):
        pass

    @solid
    def solid_c(_):
        pass

    @pipeline(hook_defs={hook_b_generic})
    def a_pipeline():
        solid_a()
        solid_b()
        solid_c()

    result = execute_pipeline(a_pipeline.with_hooks({hook_a_generic}))
    assert result.success
    # the hook should run on all solids
    assert called_hook_to_solids == {
        "hook_b_generic": {"solid_b", "solid_a", "solid_c"},
        "hook_a_generic": {"solid_b", "solid_a", "solid_c"},
    }


def test_hook_on_pipeline_def_with_composite_solids():

    called_hook_to_step_keys = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_step_keys[context.hook_def.name].add(context.step.key)
        return HookExecutionResult("hook_a_generic")

    @solid
    def two(_):
        return 1

    @solid
    def add_one(_, num):
        return num + 1

    @composite_solid
    def add_two():
        adder_1 = add_one.alias("adder_1")
        adder_2 = add_one.alias("adder_2")

        return adder_2(adder_1(two()))

    @pipeline
    def a_pipeline():
        add_two()

    hooked_pipeline = a_pipeline.with_hooks({hook_a_generic})
    # hooked_pipeline should be a copy of the original pipeline
    assert hooked_pipeline.top_level_solid_defs == a_pipeline.top_level_solid_defs
    assert hooked_pipeline.all_solid_defs == a_pipeline.all_solid_defs

    result = execute_pipeline(hooked_pipeline)
    assert result.success
    # the hook should run on all steps
    assert called_hook_to_step_keys["hook_a_generic"] == set(
        [i.step_key for i in filter(lambda i: i.is_step_event, result.event_list)]
    )


def test_hook_decorate_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult("hook_a_generic")

    @success_hook
    def hook_b_success(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)

    @failure_hook
    def hook_c_failure(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)

    @solid
    def solid_a(_):
        pass

    @solid
    def solid_b(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @hook_c_failure
    @hook_b_success
    @hook_a_generic
    @pipeline
    def a_pipeline():
        solid_a()
        failed_solid()
        solid_b()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {"solid_a", "solid_b", "failed_solid"}
    # a success hook runs on all succeeded solids
    assert called_hook_to_solids["hook_b_success"] == {"solid_a", "solid_b"}
    # a failure hook runs on all failed solids
    assert called_hook_to_solids["hook_c_failure"] == {"failed_solid"}


def test_hook_on_pipeline_def_and_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult("hook_a_generic")

    @success_hook
    def hook_b_success(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)

    @failure_hook
    def hook_c_failure(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)

    @solid
    def solid_a(_):
        pass

    @solid
    def solid_b(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @hook_a_generic
    @pipeline
    def a_pipeline():
        solid_a.with_hooks({hook_b_success})()
        failed_solid.with_hooks({hook_c_failure})()
        # "hook_a_generic" should run on "solid_b" only once
        solid_b.with_hooks({hook_a_generic})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {"solid_a", "solid_b", "failed_solid"}
    # a success hook runs on "solid_a"
    assert called_hook_to_solids["hook_b_success"] == {"solid_a"}
    # a failure hook runs on "failed_solid"
    assert called_hook_to_solids["hook_c_failure"] == {"failed_solid"}
    hook_events = list(filter(lambda event: event.is_hook_event, result.event_list))
    # same hook will run once on the same solid invocation
    assert len(hook_events) == 5


def test_hook_context_config_schema():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.solid_config == {"config_1": 1}
        return HookExecutionResult("a_hook")

    @solid(config_schema={"config_1": Int})
    def a_solid(_):
        pass

    @pipeline
    def a_pipeline():
        a_solid.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(
        a_pipeline, run_config={"solids": {"a_solid": {"config": {"config_1": 1}}}}
    )
    assert result.success
    assert called_hook_to_solids["a_hook"] == {"a_solid"}


def test_hook_resource_mismatch():
    @event_list_hook(required_resource_keys={"b"})
    def a_hook(context, _):
        assert context.resources.resource_a == 1
        return HookExecutionResult("a_hook")

    @solid
    def a_solid(_):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='Resource "b" is required by hook "a_hook"'
    ):

        @a_hook
        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def _():
            a_solid()

    with pytest.raises(
        DagsterInvalidDefinitionError, match='Resource "b" is required by hook "a_hook"'
    ):

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def _():
            a_solid.with_hooks({a_hook})()


def test_hook_subpipeline():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult("hook_a_generic")

    @solid
    def solid_a(_):
        pass

    @solid
    def solid_b(_):
        pass

    @hook_a_generic
    @pipeline
    def a_pipeline():
        solid_a()
        solid_b()

    result = execute_pipeline(a_pipeline)
    assert result.success
    # a generic hook runs on all solids
    assert called_hook_to_solids["hook_a_generic"] == {"solid_a", "solid_b"}

    called_hook_to_solids = defaultdict(set)

    result = execute_pipeline(a_pipeline, solid_selection=["solid_a"])
    assert result.success
    assert called_hook_to_solids["hook_a_generic"] == {"solid_a"}
