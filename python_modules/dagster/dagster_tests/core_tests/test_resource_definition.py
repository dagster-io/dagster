from dagster import (
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    String,
    execute_pipeline,
    resource,
    solid,
)


def define_string_resource():
    return ResourceDefinition(
        config_field=Field(String), resource_fn=lambda init_context: init_context.resource_config
    )


def test_basic_resource():
    called = {}

    @solid(resources={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    pipeline_def = PipelineDefinition(
        name='with_a_resource',
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'a_string': define_string_resource()})
        },
    )

    result = execute_pipeline(
        pipeline_def, {'context': {'default': {'resources': {'a_string': {'config': 'foo'}}}}}
    )

    assert result.success
    assert called['yup']


def test_yield_resource():
    called = {}

    @solid(resources={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    def _do_resource(init_context):
        yield init_context.resource_config

    yield_string_resource = ResourceDefinition(config_field=Field(String), resource_fn=_do_resource)

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'a_string': yield_string_resource})
        },
    )

    result = execute_pipeline(
        pipeline_def, {'context': {'default': {'resources': {'a_string': {'config': 'foo'}}}}}
    )

    assert result.success
    assert called['yup']


def test_yield_multiple_resources():
    called = {}

    saw = []

    @solid(resources={'string_one', 'string_two'})
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
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={'string_one': yield_string_resource, 'string_two': yield_string_resource}
            )
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}
                }
            }
        },
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

    @solid(resources={'string_one', 'string_two'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.string_one == 'foo'
        assert context.resources.string_two == 'bar'

    @resource(Field(String))
    def yielding_string_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={
                    'string_one': yielding_string_resource,
                    'string_two': yielding_string_resource,
                }
            )
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}
                }
            }
        },
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

    @solid(resources={'returned_string', 'yielded_string'})
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
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={
                    'yielded_string': yield_string_resource,
                    'returned_string': return_string_resource,
                }
            )
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {
                        'returned_string': {'config': 'foo'},
                        'yielded_string': {'config': 'bar'},
                    }
                }
            }
        },
    )

    assert result.success
    assert called['yup']
    # could be processed in any order in python 2
    assert 'before yield bar' in saw[0] or 'before return foo' in saw[0]
    assert 'before yield bar' in saw[1] or 'before return foo' in saw[1]
    assert 'after yield bar' in saw[2]


def test_none_resource():
    called = {}

    @solid(resources={'test_null'})
    def solid_test_null(context):
        assert context.resources.test_null is None
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_none_resource',
        solids=[solid_test_null],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={'test_null': ResourceDefinition.none_resource()}
            )
        },
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert called['yup']


def test_string_resource():
    called = {}

    @solid(resources={'test_string'})
    def solid_test_string(context):
        assert context.resources.test_string == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_string_resource',
        solids=[solid_test_string],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={'test_string': ResourceDefinition.string_resource()}
            )
        },
    )

    result = execute_pipeline(
        pipeline, {'context': {'default': {'resources': {'test_string': {'config': 'foo'}}}}}
    )

    assert result.success
    assert called['yup']


def test_no_config_resource_pass_none():
    called = {}

    @resource(None)
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(resources={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solids=[check_thing],
        context_definitions={
            'default': PipelineContextDefinition(resources={'return_thing': return_thing})
        },
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

    @solid(resources={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solids=[check_thing],
        context_definitions={
            'default': PipelineContextDefinition(resources={'return_thing': return_thing})
        },
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

    @solid(resources={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solids=[check_thing],
        context_definitions={
            'default': PipelineContextDefinition(resources={'return_thing': return_thing})
        },
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_definition():
    called = {}

    def _return_thing_resource_fn(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(resources={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solids=[check_thing],
        context_definitions={
            'default': PipelineContextDefinition(
                resources={'return_thing': ResourceDefinition(_return_thing_resource_fn)}
            )
        },
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']
