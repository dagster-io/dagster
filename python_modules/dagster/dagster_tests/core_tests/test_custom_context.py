import uuid

import pytest

from dagster import (
    Dict,
    ExecutionContext,
    Field,
    OutputDefinition,
    PipelineConfigEvaluationError,
    PipelineContextDefinition,
    PipelineDefinition,
    String,
    execute_pipeline,
    lambda_solid,
    solid,
)


from dagster.utils.logging import INFO

# protected variable. need to test loggers
# pylint: disable=W0212


def test_default_context():
    called = {}

    @solid(inputs=[], outputs=[OutputDefinition()])
    def default_context_transform(context):
        called['yes'] = True
        for logger in context.log.loggers:
            assert logger.level == INFO

    pipeline = PipelineDefinition(solids=[default_context_transform])
    execute_pipeline(pipeline)

    assert called['yes']


def test_run_id():
    called = {}

    def construct_context(context):
        called['yes'] = True
        assert uuid.UUID(context.run_id)
        return ExecutionContext()

    pipeline = PipelineDefinition(
        solids=[],
        context_definitions={'default': PipelineContextDefinition(context_fn=construct_context)},
    )
    execute_pipeline(pipeline)

    assert called['yes']


def test_default_context_with_log_level():
    @solid(inputs=[], outputs=[OutputDefinition()])
    def default_context_transform(context):
        for logger in context.log.loggers:
            assert logger.level == INFO

    pipeline = PipelineDefinition(solids=[default_context_transform])
    execute_pipeline(
        pipeline, environment_dict={'context': {'default': {'config': {'log_level': 'INFO'}}}}
    )

    with pytest.raises(PipelineConfigEvaluationError):
        execute_pipeline(
            pipeline, environment_dict={'context': {'default': {'config': {'log_level': 2}}}}
        )


def test_default_value():
    def _get_config_test_solid(config_key, config_value):
        @solid(inputs=[], outputs=[OutputDefinition()])
        def config_test(context):
            assert context.resources == {config_key: config_value}

        return config_test

    pipeline = PipelineDefinition(
        solids=[_get_config_test_solid('field_one', 'heyo')],
        context_definitions={
            'custom_one': PipelineContextDefinition(
                config_field=Field(
                    Dict(
                        {
                            'field_one': Field(
                                dagster_type=String, is_optional=True, default_value='heyo'
                            )
                        }
                    )
                ),
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
            )
        },
    )

    execute_pipeline(pipeline, environment_dict={'context': {'custom_one': {}}})

    execute_pipeline(pipeline, environment_dict={'context': {'custom_one': None}})


def test_custom_contexts():
    @solid(inputs=[], outputs=[OutputDefinition()])
    def custom_context_transform(context):
        assert context.resources == {'field_one': 'value_two'}

    pipeline = PipelineDefinition(
        solids=[custom_context_transform],
        context_definitions={
            'custom_one': PipelineContextDefinition(
                config_field=Field(Dict({'field_one': Field(dagster_type=String)})),
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
            ),
            'custom_two': PipelineContextDefinition(
                config_field=Field(Dict({'field_one': Field(dagster_type=String)})),
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
            ),
        },
    )
    environment_one = {'context': {'custom_one': {'config': {'field_one': 'value_two'}}}}

    execute_pipeline(pipeline, environment_dict=environment_one)

    environment_two = {'context': {'custom_two': {'config': {'field_one': 'value_two'}}}}

    execute_pipeline(pipeline, environment_dict=environment_two)


def test_yield_context():
    events = []

    @solid(inputs=[], outputs=[OutputDefinition()])
    def custom_context_transform(context):
        assert context.resources == {'field_one': 'value_two'}
        assert context.get_tag('foo') == 'bar'  # pylint: disable=W0212
        events.append('during')

    def _yield_context(init_context):
        events.append('before')
        tags = {'foo': 'bar'}
        context = ExecutionContext(resources=init_context.context_config, tags=tags)
        yield context
        events.append('after')

    pipeline = PipelineDefinition(
        solids=[custom_context_transform],
        context_definitions={
            'custom_one': PipelineContextDefinition(
                config_field=Field(Dict({'field_one': Field(dagster_type=String)})),
                context_fn=_yield_context,
            )
        },
    )

    environment_one = {'context': {'custom_one': {'config': {'field_one': 'value_two'}}}}

    execute_pipeline(pipeline, environment_dict=environment_one)

    assert events == ['before', 'during', 'after']


def test_invalid_context():
    @lambda_solid
    def never_transform():
        raise Exception('should never execute')

    default_context_pipeline = PipelineDefinition(
        name='default_context_pipeline', solids=[never_transform]
    )

    environment_context_not_found = {'context': {'not_found': {}}}

    with pytest.raises(
        PipelineConfigEvaluationError, match='Undefined field "not_found" at path root:context'
    ):
        execute_pipeline(default_context_pipeline, environment_dict=environment_context_not_found)

    environment_field_name_mismatch = {'context': {'default': {'config': {'unexpected': 'value'}}}}

    with pytest.raises(PipelineConfigEvaluationError, match='Undefined field "unexpected"'):
        execute_pipeline(default_context_pipeline, environment_dict=environment_field_name_mismatch)

    with_argful_context_pipeline = PipelineDefinition(
        solids=[never_transform],
        context_definitions={
            'default': PipelineContextDefinition(
                config_field=Field(Dict({'string_field': Field(String)})),
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
            )
        },
    )

    environment_no_config_error = {'context': {'default': {'config': {}}}}

    with pytest.raises(
        PipelineConfigEvaluationError,
        # match=(
        #     'Error 1: Missing required field  "string_field" at path '
        #     'root:context:default:config Expected: "{ string_field: String }"'
        # ),
    ) as pe_info_one:
        execute_pipeline(with_argful_context_pipeline, environment_dict=environment_no_config_error)

    assert len(pe_info_one.value.errors) == 1

    assert pe_info_one.value.errors[0].message == (
        '''Missing required field "string_field" at path root:context:default:config '''
        '''Available Fields: "['string_field']".'''
    )

    environment_type_mismatch_error = {'context': {'default': {'config': {'string_field': 1}}}}

    with pytest.raises(
        PipelineConfigEvaluationError,
        match=(
            'Error 1: Type failure at path "root:context:default:config:string_field" '
            'on type "String". Value at path '
            'root:context:default:config:string_field is not valid. Expected "String".'
        ),
    ):
        execute_pipeline(
            with_argful_context_pipeline, environment_dict=environment_type_mismatch_error
        )
