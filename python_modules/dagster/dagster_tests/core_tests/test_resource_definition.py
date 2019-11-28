import uuid

import pytest

from dagster import (
    DagsterResourceFunctionError,
    Field,
    ModeDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidInvocation,
    String,
    execute_pipeline,
    execute_pipeline_iterator,
    resource,
    solid,
)
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun


def define_string_resource():
    return ResourceDefinition(
        config_field=Field(String), resource_fn=lambda init_context: init_context.resource_config
    )


def test_basic_resource():
    called = {}

    @solid(required_resource_keys={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    pipeline_def = PipelineDefinition(
        name='with_a_resource',
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(resource_defs={'a_string': define_string_resource()})],
    )

    result = execute_pipeline(pipeline_def, {'resources': {'a_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_yield_resource():
    called = {}

    @solid(required_resource_keys={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    def _do_resource(init_context):
        yield init_context.resource_config

    yield_string_resource = ResourceDefinition(config_field=Field(String), resource_fn=_do_resource)

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(resource_defs={'a_string': yield_string_resource})],
    )

    result = execute_pipeline(pipeline_def, {'resources': {'a_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_yield_multiple_resources():
    called = {}

    saw = []

    @solid(required_resource_keys={'string_one', 'string_two'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.string_one == 'foo'
        assert context.resources.string_two == 'bar'

    def _do_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    yield_string_resource = ResourceDefinition(config_field=Field(String), resource_fn=_do_resource)

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'string_one': yield_string_resource,
                    'string_two': yield_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    assert len(saw) == 4

    assert 'before yield' in saw[0]
    assert 'before yield' in saw[1]
    assert 'after yield' in saw[2]
    assert 'after yield' in saw[3]


def test_resource_decorator():
    called = {}

    saw = []

    @solid(required_resource_keys={'string_one', 'string_two'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.string_one == 'foo'
        assert context.resources.string_two == 'bar'

    @resource(config_field=Field(String))
    def yielding_string_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'string_one': yielding_string_resource,
                    'string_two': yielding_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    assert len(saw) == 4

    assert 'before yield' in saw[0]
    assert 'before yield' in saw[1]
    assert 'after yield' in saw[2]
    assert 'after yield' in saw[3]


def test_mixed_multiple_resources():
    called = {}

    saw = []

    @solid(required_resource_keys={'returned_string', 'yielded_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.returned_string == 'foo'
        assert context.resources.yielded_string == 'bar'

    def _do_yield_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    yield_string_resource = ResourceDefinition(
        config_field=Field(String), resource_fn=_do_yield_resource
    )

    def _do_return_resource(init_context):
        saw.append('before return ' + init_context.resource_config)
        return init_context.resource_config

    return_string_resource = ResourceDefinition(
        config_field=Field(String), resource_fn=_do_return_resource
    )

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'yielded_string': yield_string_resource,
                    'returned_string': return_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'returned_string': {'config': 'foo'}, 'yielded_string': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    # could be processed in any order in python 2
    assert 'before yield bar' in saw[0] or 'before return foo' in saw[0]
    assert 'before yield bar' in saw[1] or 'before return foo' in saw[1]
    assert 'after yield bar' in saw[2]


def test_none_resource():
    called = {}

    @solid(required_resource_keys={'test_null'})
    def solid_test_null(context):
        assert context.resources.test_null is None
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_none_resource',
        solid_defs=[solid_test_null],
        mode_defs=[ModeDefinition(resource_defs={'test_null': ResourceDefinition.none_resource()})],
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert called['yup']


def test_string_resource():
    called = {}

    @solid(required_resource_keys={'test_string'})
    def solid_test_string(context):
        assert context.resources.test_string == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_string_resource',
        solid_defs=[solid_test_string],
        mode_defs=[
            ModeDefinition(resource_defs={'test_string': ResourceDefinition.string_resource()})
        ],
    )

    result = execute_pipeline(pipeline, {'resources': {'test_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_no_config_resource_pass_none():
    called = {}

    @resource(None)
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_no_arg():
    called = {}

    @resource()
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_bare_no_arg():
    called = {}

    @resource
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_definition():
    called = {}

    def _return_thing_resource_fn(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[
            ModeDefinition(
                resource_defs={'return_thing': ResourceDefinition(_return_thing_resource_fn)}
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_resource_cleanup():
    called = {}

    def _cleanup_resource_fn(_init_context):
        called['creation'] = True
        yield True
        called['cleanup'] = True

    @solid(required_resource_keys={'resource_with_cleanup'})
    def check_resource_created(context):
        called['solid'] = True
        assert context.resources.resource_with_cleanup is True

    pipeline = PipelineDefinition(
        name='test_resource_cleanup',
        solid_defs=[check_resource_created],
        mode_defs=[
            ModeDefinition(
                resource_defs={'resource_with_cleanup': ResourceDefinition(_cleanup_resource_fn)}
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called['creation'] is True
    assert called['solid'] is True
    assert called['cleanup'] is True


def test_stacked_resource_cleanup():
    called = []

    def _cleanup_resource_fn_1(_init_context):
        called.append('creation_1')
        yield True
        called.append('cleanup_1')

    def _cleanup_resource_fn_2(_init_context):
        called.append('creation_2')
        yield True
        called.append('cleanup_2')

    @solid(required_resource_keys={'resource_with_cleanup_1', 'resource_with_cleanup_2'})
    def check_resource_created(context):
        called.append('solid')
        assert context.resources.resource_with_cleanup_1 is True
        assert context.resources.resource_with_cleanup_2 is True

    pipeline = PipelineDefinition(
        name='test_resource_cleanup',
        solid_defs=[check_resource_created],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'resource_with_cleanup_1': ResourceDefinition(_cleanup_resource_fn_1),
                    'resource_with_cleanup_2': ResourceDefinition(_cleanup_resource_fn_2),
                }
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called == ['creation_1', 'creation_2', 'solid', 'cleanup_2', 'cleanup_1']


def test_resource_init_failure():
    @resource
    def failing_resource(_init_context):
        raise Exception('Uh oh')

    @solid(required_resource_keys={'failing_resource'})
    def failing_resource_solid(_context):
        pass

    pipeline = PipelineDefinition(
        name='test_resource_init_failure',
        solid_defs=[failing_resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'failing_resource': failing_resource})],
    )

    res = execute_pipeline(pipeline, raise_on_error=False)

    assert res.event_list[0].event_type_value == 'PIPELINE_INIT_FAILURE'

    execution_plan = create_execution_plan(pipeline)
    run_id = str(uuid.uuid4())
    pipeline_run = PipelineRun.create_empty_run(pipeline.name, run_id)

    step_events = execute_plan(
        execution_plan, pipeline_run=pipeline_run, instance=DagsterInstance.ephemeral()
    )

    assert step_events[0].event_type_value == 'PIPELINE_INIT_FAILURE'

    # Test the pipeline init failure event fires even if we are raising errors
    events = []
    try:
        for event in execute_pipeline_iterator(pipeline):
            events.append(event)
    except DagsterResourceFunctionError:
        pass

    assert len(events) == 1
    assert events[0].event_type_value == 'PIPELINE_INIT_FAILURE'


# https://github.com/dagster-io/dagster/issues/1949
@pytest.mark.xfail
def test_with_resource_mapper_fn_with_required_keys():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_c_alias(_):
        resources_initted['c'] = True
        yield 'C'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'
        return context.resources.a

    @solid(required_resource_keys={'c'})
    def consumes_resource_c(context):
        assert context.resources.c == 'C'
        return context.resources.c

    def _resource_mapper_fn(resources, _resource_deps):
        return {'a': resources['a'], 'c': resources['c_alias']}

    pipeline_with_resource_mapper = PipelineDefinition(
        solid_defs=[consumes_resource_a, consumes_resource_c],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'c_alias': resource_c_alias})],
        dependencies={
            SolidInvocation('consumes_resource_a'): {},
            SolidInvocation(
                'consumes_resource_c',
                alias='consumes_resource_c',
                resource_mapper_fn=_resource_mapper_fn,
            ): {},
        },
    )

    assert execute_pipeline(pipeline_with_resource_mapper).success


# https://github.com/dagster-io/dagster/issues/1950
@pytest.mark.xfail
def test_with_resource_mapper_fn_without_required_keys():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted['a'] = True
        yield 'A'

    @resource
    def resource_c_alias(_):
        resources_initted['c'] = True
        yield 'C'

    @solid(required_resource_keys={'a'})
    def consumes_resource_a(context):
        assert context.resources.a == 'A'
        return context.resources.a

    @solid
    def consumes_resource_c(context):
        assert context.resources.c == 'C'
        return context.resources.c

    def _resource_mapper_fn(resources, _resource_deps):
        return {'a': resources['a'], 'c': resources['c_alias']}

    pipeline_with_resource_mapper = PipelineDefinition(
        solid_defs=[consumes_resource_a, consumes_resource_c],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'c_alias': resource_c_alias})],
        dependencies={
            SolidInvocation('consumes_resource_a'): {},
            SolidInvocation(
                'consumes_resource_c',
                alias='consumes_resource_c',
                resource_mapper_fn=_resource_mapper_fn,
            ): {},
        },
    )

    assert execute_pipeline(pipeline_with_resource_mapper).success
