from dagster import (
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    execute_pipeline,
    solid,
    types,
)


def define_string_resource():
    return ResourceDefinition(
        config_field=types.Field(types.String),
        resource_fn=lambda info: info.config,
    )


def test_basic_resource():
    called = {}

    @solid
    def a_solid(info):
        called['yup'] = True
        assert info.context.resources.a_string == 'foo'

    pipeline_def = PipelineDefinition(
        name='with_a_resource',
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'a_string': define_string_resource()}),
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {
                        'a_string': {
                            'config': 'foo',
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_yield_resource():
    called = {}

    @solid
    def a_solid(info):
        called['yup'] = True
        assert info.context.resources.a_string == 'foo'

    def _do_resource(info):
        yield info.config

    yield_string_resource = ResourceDefinition(
        config_field=types.Field(types.String),
        resource_fn=_do_resource,
    )

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solids=[a_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'a_string': yield_string_resource}),
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {
                        'a_string': {
                            'config': 'foo',
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_yield_multiple_resources():
    called = {}

    saw = []

    @solid
    def a_solid(info):
        called['yup'] = True
        assert info.context.resources.string_one == 'foo'
        assert info.context.resources.string_two == 'bar'

    def _do_resource(info):
        saw.append('before yield ' + info.config)
        yield info.config
        saw.append('after yield ' + info.config)

    yield_string_resource = ResourceDefinition(
        config_field=types.Field(types.String),
        resource_fn=_do_resource,
    )

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solids=[a_solid],
        context_definitions={
            'default':
            PipelineContextDefinition(
                resources={
                    'string_one': yield_string_resource,
                    'string_two': yield_string_resource,
                },
            ),
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {
                        'string_one': {
                            'config': 'foo',
                        },
                        'string_two': {
                            'config': 'bar',
                        },
                    },
                },
            },
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

    @solid
    def a_solid(info):
        called['yup'] = True
        assert info.context.resources.returned_string == 'foo'
        assert info.context.resources.yielded_string == 'bar'

    def _do_yield_resource(info):
        saw.append('before yield ' + info.config)
        yield info.config
        saw.append('after yield ' + info.config)

    yield_string_resource = ResourceDefinition(
        config_field=types.Field(types.String),
        resource_fn=_do_yield_resource,
    )

    def _do_return_resource(info):
        saw.append('before return ' + info.config)
        return info.config

    return_string_resource = ResourceDefinition(
        config_field=types.Field(types.String),
        resource_fn=_do_return_resource,
    )

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solids=[a_solid],
        context_definitions={
            'default':
            PipelineContextDefinition(
                resources={
                    'yielded_string': yield_string_resource,
                    'returned_string': return_string_resource,
                },
            ),
        },
    )

    result = execute_pipeline(
        pipeline_def,
        {
            'context': {
                'default': {
                    'resources': {
                        'returned_string': {
                            'config': 'foo',
                        },
                        'yielded_string': {
                            'config': 'bar',
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']
    # could be processed in any order in python 2
    assert 'before yield bar' in saw[0] or 'before return foo' in saw[0]
    assert 'before yield bar' in saw[1] or 'before return foo' in saw[1]
    assert 'after yield bar' in saw[2]


def test_null_resource():
    called = {}

    @solid
    def solid_test_null(info):
        assert info.context.resources.test_null is None
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_null_resource',
        solids=[solid_test_null],
        context_definitions={
            'default':
            PipelineContextDefinition(
                resources={
                    'test_null': ResourceDefinition.null_resource(),
                },
            ),
        },
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert called['yup']


def test_string_resource():
    called = {}

    @solid
    def solid_test_string(info):
        assert info.context.resources.test_string == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_string_resource',
        solids=[solid_test_string],
        context_definitions={
            'default':
            PipelineContextDefinition(
                resources={
                    'test_string': ResourceDefinition.string_resource(),
                },
            ),
        },
    )

    result = execute_pipeline(
        pipeline,
        {
            'context': {
                'default': {
                    'resources': {
                        'test_string': {
                            'config': 'foo'
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']
