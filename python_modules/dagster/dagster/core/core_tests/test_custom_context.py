import pytest

from dagster import (
    ConfigDefinition,
    ExecutionContext,
    Field,
    OutputDefinition,
    PipelineDefinition,
    PipelineContextDefinition,
    config,
    execute_pipeline,
    transform,
    types,
    with_context,
)
from dagster.core.errors import (DagsterTypeError, DagsterInvariantViolationError)
from dagster.utils.logging import (INFO, ERROR)

# protected variable. need to test loggers
# pylint: disable=W0212


def test_default_context():
    @transform(
        inputs=[],
        outputs=[OutputDefinition()],
    )
    @with_context
    def default_context_transform(context):
        for logger in context._logger.loggers:
            assert logger.level == ERROR

    pipeline = PipelineDefinition(solids=[default_context_transform])
    execute_pipeline(
        pipeline, environment=config.Environment(context=config.Context('default', {}))
    )


def test_default_context_with_log_level():
    @transform(
        inputs=[],
        outputs=[OutputDefinition()],
    )
    @with_context
    def default_context_transform(context):
        for logger in context._logger.loggers:
            assert logger.level == INFO

    pipeline = PipelineDefinition(solids=[default_context_transform])
    execute_pipeline(
        pipeline,
        environment=config.Environment(context=config.Context('default', {'log_level': 'INFO'}))
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            pipeline,
            environment=config.Environment(context=config.Context('default', {'log_level': 2}))
        )


def test_default_value():
    def _get_config_test_solid(config_key, config_value):
        @transform(
            inputs=[],
            outputs=[OutputDefinition()],
        )
        @with_context
        def config_test(context):
            assert context.resources == {config_key: config_value}

        return config_test

    pipeline = PipelineDefinition(
        solids=[_get_config_test_solid('field_one', 'heyo')],
        context_definitions={
            'custom_one':
            PipelineContextDefinition(
                config_def=ConfigDefinition.config_dict(
                    {
                        'field_one':
                        Field(
                            dagster_type=types.String,
                            is_optional=True,
                            default_value='heyo',
                        )
                    }
                ),
                context_fn=lambda _pipeline, config_value: ExecutionContext(resources=config_value),
            ),
        }
    )

    execute_pipeline(
        pipeline, environment=config.Environment(context=config.Context('custom_one', {}))
    )


def test_custom_contexts():
    @transform(
        inputs=[],
        outputs=[OutputDefinition()],
    )
    @with_context
    def custom_context_transform(context):
        assert context.resources == {'field_one': 'value_two'}

    pipeline = PipelineDefinition(
        solids=[custom_context_transform],
        context_definitions={
            'custom_one':
            PipelineContextDefinition(
                config_def=ConfigDefinition.config_dict(
                    {
                        'field_one': Field(dagster_type=types.String)
                    }
                ),
                context_fn=lambda _pipeline, config_value: ExecutionContext(resources=config_value),
            ),
            'custom_two':
            PipelineContextDefinition(
                config_def=ConfigDefinition.config_dict(
                    {
                        'field_one': Field(dagster_type=types.String)
                    }
                ),
                context_fn=lambda _pipeline, config_value: ExecutionContext(resources=config_value),
            )
        },
    )

    environment_one = config.Environment(
        context=config.Context('custom_one', {'field_one': 'value_two'})
    )

    execute_pipeline(pipeline, environment=environment_one)

    environment_two = config.Environment(
        context=config.Context('custom_two', {'field_one': 'value_two'})
    )

    execute_pipeline(pipeline, environment=environment_two)


def test_yield_context():
    events = []

    @transform(
        inputs=[],
        outputs=[OutputDefinition()],
    )
    @with_context
    def custom_context_transform(context):
        assert context.resources == {'field_one': 'value_two'}
        assert context._context_dict['foo'] == 'bar'  # pylint: disable=W0212
        events.append('during')

    def _yield_context(_pipeline, config_value):
        events.append('before')
        context = ExecutionContext(resources=config_value)
        with context.value('foo', 'bar'):
            yield context
        events.append('after')

    pipeline = PipelineDefinition(
        solids=[custom_context_transform],
        context_definitions={
            'custom_one':
            PipelineContextDefinition(
                config_def=ConfigDefinition.config_dict(
                    {
                        'field_one': Field(dagster_type=types.String)
                    }
                ),
                context_fn=_yield_context,
            ),
        }
    )

    environment_one = config.Environment(
        context=config.Context('custom_one', {'field_one': 'value_two'})
    )

    execute_pipeline(pipeline, environment=environment_one)

    assert events == ['before', 'during', 'after']


# TODO: reenable pending the ability to specific optional arguments
# https://github.com/dagster-io/dagster/issues/56
def test_invalid_context():
    @transform(
        inputs=[],
        outputs=[OutputDefinition()],
    )
    def never_transform():
        raise Exception('should never execute')

    default_context_pipeline = PipelineDefinition(solids=[never_transform])

    environment_context_not_found = config.Environment(context=config.Context('not_found', {}))

    with pytest.raises(DagsterInvariantViolationError, message='Context not_found not found'):
        execute_pipeline(
            default_context_pipeline,
            environment=environment_context_not_found,
            throw_on_error=True
        )

    environment_field_name_mismatch = config.Environment(
        context=config.Context('default', {'unexpected': 'value'})
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            default_context_pipeline,
            environment=environment_field_name_mismatch,
            throw_on_error=True
        )

    with_argful_context_pipeline = PipelineDefinition(
        solids=[never_transform],
        context_definitions={
            'default':
            PipelineContextDefinition(
                config_def=ConfigDefinition.config_dict(
                    {
                        'string_field': Field(types.String)
                    }
                ),
                context_fn=lambda _pipeline, _config_value: _config_value
            )
        }
    )

    environment_no_config_error = config.Environment(context=config.Context('default', {}))

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            with_argful_context_pipeline,
            environment=environment_no_config_error,
            throw_on_error=True
        )

    environment_type_mismatch_error = config.Environment(
        context=config.Context('default', {'string_field': 1})
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            with_argful_context_pipeline,
            environment=environment_type_mismatch_error,
            throw_on_error=True
        )
