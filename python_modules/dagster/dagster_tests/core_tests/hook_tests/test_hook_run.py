from collections import defaultdict

from dagster import ModeDefinition, execute_pipeline, pipeline, resource, solid
from dagster.core.definitions import failure_hook, success_hook
from dagster.core.definitions.decorators.hook import event_list_hook
from dagster.core.definitions.events import HookExecutionResult


class SomeUserException(Exception):
    pass


@resource
def resource_a(_init_context):
    return 1


def test_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook(required_resource_keys={'resource_a'})
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1
        return HookExecutionResult('a_hook')

    @solid
    def a_solid(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'resource_a': resource_a})])
    def a_pipeline():
        a_solid.with_hooks(hook_defs={a_hook})()
        a_solid.alias('solid_with_hook').with_hooks(hook_defs={a_hook})()
        a_solid.alias('solid_without_hook')()

    result = execute_pipeline(a_pipeline)
    assert result.success
    assert called_hook_to_solids['a_hook'] == {'a_solid', 'solid_with_hook'}


def test_success_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @success_hook(required_resource_keys={'resource_a'})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def a_solid(_):
        pass

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'resource_a': resource_a})])
    def a_pipeline():
        a_solid.with_hooks(hook_defs={a_hook})()
        a_solid.alias('solid_with_hook').with_hooks(hook_defs={a_hook})()
        a_solid.alias('solid_without_hook')()
        failed_solid.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids['a_hook'] == {'a_solid', 'solid_with_hook'}


def test_failure_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @failure_hook(required_resource_keys={'resource_a'})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        assert context.resources.resource_a == 1

    @solid
    def failed_solid(_):
        raise SomeUserException()

    @solid
    def a_succeeded_solid(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'resource_a': resource_a})])
    def a_pipeline():
        failed_solid.with_hooks(hook_defs={a_hook})()
        failed_solid.alias('solid_with_hook').with_hooks(hook_defs={a_hook})()
        failed_solid.alias('solid_without_hook')()
        a_succeeded_solid.with_hooks(hook_defs={a_hook})()

    result = execute_pipeline(a_pipeline, raise_on_error=False)
    assert not result.success
    assert called_hook_to_solids['a_hook'] == {'failed_solid', 'solid_with_hook'}


def test_hook_on_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult('hook_a_generic')

    @solid
    def solid_a(_):
        pass

    @solid
    def solid_b(_):
        pass

    @solid
    def solid_c(_):
        pass

    @pipeline
    def a_pipeline():
        solid_a()
        solid_b()
        solid_c()

    result = execute_pipeline(a_pipeline.with_hooks({hook_a_generic}))
    assert result.success
    # the hook should run on all solids
    assert called_hook_to_solids['hook_a_generic'] == {'solid_a', 'solid_b', 'solid_c'}


def test_hook_decorate_pipeline_def():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult('hook_a_generic')

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
    assert called_hook_to_solids['hook_a_generic'] == {'solid_a', 'solid_b', 'failed_solid'}
    # a success hook runs on all succeeded solids
    assert called_hook_to_solids['hook_b_success'] == {'solid_a', 'solid_b'}
    # a failure hook runs on all failed solids
    assert called_hook_to_solids['hook_c_failure'] == {'failed_solid'}


def test_hook_on_pipeline_def_and_solid_instance():

    called_hook_to_solids = defaultdict(set)

    @event_list_hook
    def hook_a_generic(context, _):
        called_hook_to_solids[context.hook_def.name].add(context.solid.name)
        return HookExecutionResult('hook_a_generic')

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
    assert called_hook_to_solids['hook_a_generic'] == {'solid_a', 'solid_b', 'failed_solid'}
    # a success hook runs on "solid_a"
    assert called_hook_to_solids['hook_b_success'] == {'solid_a'}
    # a failure hook runs on "failed_solid"
    assert called_hook_to_solids['hook_c_failure'] == {'failed_solid'}
    hook_events = list(filter(lambda event: event.is_hook_event, result.event_list))
    # same hook will run once on the same solid invocation
    assert len(hook_events) == 5
