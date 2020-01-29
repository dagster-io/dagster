import pytest

from dagster import (
    DagsterUnknownResourceError,
    ModeDefinition,
    ResourceDefinition,
    RunConfig,
    composite_solid,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)


def get_resource_init_pipeline(resources_initted):
    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_b(_):
        resources_initted['b'] = True
        yield 'B'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'

    @solid(required_resource_keys={'b'})
    def consumes_resource_b(context):
        assert context.resources.b == 'B'

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b,})],)
    def selective_init_test_pipeline():
        consumes_resource_a()
        consumes_resource_b()

    return selective_init_test_pipeline


def test_filter_out_resources():
    @solid(required_resource_keys={'a'})
    def requires_resource_a(context):
        assert context.resources.a
        assert not hasattr(context.resources, 'b')

    @solid(required_resource_keys={'b'})
    def requires_resource_b(context):
        assert not hasattr(context.resources, 'a')
        assert context.resources.b

    @solid
    def not_resources(context):
        assert not hasattr(context.resources, 'a')
        assert not hasattr(context.resources, 'b')

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'a': ResourceDefinition.hardcoded_resource('foo'),
                    'b': ResourceDefinition.hardcoded_resource('bar'),
                }
            )
        ],
    )
    def room_of_requirement():
        requires_resource_a()
        requires_resource_b()
        not_resources()

    execute_pipeline(room_of_requirement)


def test_selective_init_resources():
    resources_initted = {}

    assert execute_pipeline(get_resource_init_pipeline(resources_initted)).success

    assert set(resources_initted.keys()) == {'a', 'b'}


def test_selective_init_resources_only_a():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_b(_):
        resources_initted['b'] = True
        yield 'B'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b,})],)
    def selective_init_test_pipeline():
        consumes_resource_a()

    assert execute_pipeline(selective_init_test_pipeline).success

    assert set(resources_initted.keys()) == {'a'}


def test_execution_plan_subset_strict_resources():
    resources_initted = {}

    result = execute_pipeline(
        get_resource_init_pipeline(resources_initted),
        run_config=RunConfig(step_keys_to_execute=['consumes_resource_b.compute']),
    )

    assert result.success

    assert set(resources_initted.keys()) == {'b'}


def test_solid_subset_strict_resources():
    resources_initted = {}

    selective_init_test_pipeline = get_resource_init_pipeline(resources_initted)

    result = execute_pipeline(
        selective_init_test_pipeline.build_sub_pipeline(['consumes_resource_b'])
    )
    assert result.success

    assert set(resources_initted.keys()) == {'b'}


def test_solid_subset_with_aliases_strict_resources():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_b(_):
        resources_initted['b'] = True
        yield 'B'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'

    @solid(required_resource_keys={'b'})
    def consumes_resource_b(context):
        assert context.resources.b == 'B'

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b,})],)
    def selective_init_test_pipeline():
        consumes_resource_a.alias('alias_for_a')()
        consumes_resource_b()

    result = execute_pipeline(selective_init_test_pipeline.build_sub_pipeline(['alias_for_a']))
    assert result.success

    assert set(resources_initted.keys()) == {'a'}


def create_composite_solid_pipeline(resources_initted):
    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'a'

    @resource
    def resource_b(_):
        resources_initted['b'] = True
        yield 'B'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'

    @solid(required_resource_keys={'b'})
    def consumes_resource_b(context):
        assert context.resources.b == 'B'

    @solid
    def consumes_resource_b_error(context):
        assert context.resources.b == 'B'

    @composite_solid
    def wraps_a():
        consumes_resource_a()

    @composite_solid
    def wraps_b():
        consumes_resource_b()

    @composite_solid
    def wraps_b_error():
        consumes_resource_b()
        consumes_resource_b_error()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b,})],)
    def selective_init_composite_test_pipeline():
        wraps_a()
        wraps_b()
        wraps_b_error()

    return selective_init_composite_test_pipeline


def test_solid_subset_strict_resources_within_composite():
    resources_initted = {}

    result = execute_pipeline(
        create_composite_solid_pipeline(resources_initted).build_sub_pipeline(['wraps_b'])
    )
    assert result.success

    assert set(resources_initted.keys()) == {'b'}


def test_execution_plan_subset_strict_resources_within_composite():
    resources_initted = {}

    result = execute_pipeline(
        create_composite_solid_pipeline(resources_initted),
        run_config=RunConfig(step_keys_to_execute=['wraps_b.consumes_resource_b.compute']),
    )
    assert result.success

    assert set(resources_initted.keys()) == {'b'}


def test_unknown_resource_composite_error():
    resources_initted = {}

    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(
            create_composite_solid_pipeline(resources_initted).build_sub_pipeline(['wraps_b_error'])
        )


def test_execution_plan_subset_with_aliases():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_b(_):
        resources_initted['b'] = True
        yield 'B'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'

    @solid(required_resource_keys={'b'})
    def consumes_resource_b(context):
        assert context.resources.b == 'B'

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b,})],)
    def selective_init_test_pipeline_with_alias():
        consumes_resource_a()
        consumes_resource_b.alias('b_alias')()

    assert execute_pipeline(
        selective_init_test_pipeline_with_alias,
        run_config=RunConfig(step_keys_to_execute=['b_alias.compute']),
    ).success

    assert set(resources_initted.keys()) == {'b'}


# TODO: Add test for resource mapping pending resolution of
# https://github.com/dagster-io/dagster/issues/1950 and
# https://github.com/dagster-io/dagster/issues/1949
