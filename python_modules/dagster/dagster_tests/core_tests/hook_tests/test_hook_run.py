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

    called_hook_to_solids = defaultdict(list)

    @event_list_hook(required_resource_keys={'resource_a'})
    def a_hook(context, _):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)
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
    assert 'a_solid' in called_hook_to_solids['a_hook']
    assert 'solid_with_hook' in called_hook_to_solids['a_hook']
    assert 'solid_without_hook' not in called_hook_to_solids['a_hook']


def test_success_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(list)

    @success_hook(required_resource_keys={'resource_a'})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)
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
    assert 'a_solid' in called_hook_to_solids['a_hook']
    assert 'solid_with_hook' in called_hook_to_solids['a_hook']
    assert 'solid_without_hook' not in called_hook_to_solids['a_hook']
    assert 'failed_solid' not in called_hook_to_solids['a_hook']


def test_failure_hook_on_solid_instance():

    called_hook_to_solids = defaultdict(list)

    @failure_hook(required_resource_keys={'resource_a'})
    def a_hook(context):
        called_hook_to_solids[context.hook_def.name].append(context.solid.name)
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
    assert 'failed_solid' in called_hook_to_solids['a_hook']
    assert 'solid_with_hook' in called_hook_to_solids['a_hook']
    assert 'solid_without_hook' not in called_hook_to_solids['a_hook']
    assert 'a_succeeded_solid' not in called_hook_to_solids['a_hook']
