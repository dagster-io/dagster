import pytest
import dagster
from dagster import (config, PipelineContextDefinition)
from dagster.core import types
from dagster.core.decorators import (solid, with_context)
from dagster.core.definitions import OutputDefinition
from dagster.core.execution import execute_pipeline
from dagster.core.errors import (DagsterInvariantViolationError, DagsterTypeError)


def test_default_context():
    @solid(
        inputs=[],
        output=OutputDefinition(),
    )
    @with_context
    def default_context_transform(context):
        assert context.args == {}

    pipeline = dagster.PipelineDefinition(solids=[default_context_transform])
    environment = config.Environment(sources={}, context=config.Context('default', {}))

    execute_pipeline(pipeline, environment=environment)


def test_custom_contexts():
    @solid(
        inputs=[],
        output=OutputDefinition(),
    )
    @with_context
    def custom_context_transform(context):
        assert context.args == {'arg_one': 'value_two'}

    pipeline = dagster.PipelineDefinition(
        solids=[custom_context_transform],
        context_definitions={
            'custom_one':
            PipelineContextDefinition(
                argument_def_dict={
                    'arg_one': dagster.ArgumentDefinition(dagster_type=types.String)
                },
                context_fn=lambda args: dagster.ExecutionContext(args=args),
            ),
            'custom_two':
            PipelineContextDefinition(
                argument_def_dict={
                    'arg_one': dagster.ArgumentDefinition(dagster_type=types.String)
                },
                context_fn=lambda args: dagster.ExecutionContext(args=args),
            )
        },
    )

    environment_one = config.Environment(
        sources={}, context=config.Context('custom_one', {'arg_one': 'value_two'})
    )

    execute_pipeline(pipeline, environment=environment_one)

    environment_two = config.Environment(
        sources={}, context=config.Context('custom_two', {'arg_one': 'value_two'})
    )

    execute_pipeline(pipeline, environment=environment_two)


# TODO: reenable pending the ability to specific optional arguments
# https://github.com/dagster-io/dagster/issues/56
@pytest.mark.skip
def test_invalid_context():
    @solid(
        inputs=[],
        output=OutputDefinition(),
    )
    def never_transform():
        raise Exception('should never execute')

    default_context_pipeline = dagster.PipelineDefinition(solids=[never_transform])

    environment_context_not_found = config.Environment(
        sources={}, context=config.Context('not_found', {})
    )

    with pytest.raises(DagsterInvariantViolationError, message='Context not_found not found'):
        execute_pipeline(
            default_context_pipeline,
            environment=environment_context_not_found,
            throw_on_error=True
        )

    environment_arg_name_mismatch = config.Environment(
        sources={}, context=config.Context('default', {'unexpected': 'value'})
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            default_context_pipeline,
            environment=environment_arg_name_mismatch,
            throw_on_error=True
        )

    with_argful_context_pipeline = dagster.PipelineDefinition(
        solids=[never_transform],
        context_definitions={
            'default':
            PipelineContextDefinition(
                argument_def_dict={'string_arg': types.String}, context_fn=lambda _args: _args
            )
        }
    )

    environment_no_args_error = config.Environment(
        sources={}, context=config.Context('default', {})
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            with_argful_context_pipeline,
            environment=environment_no_args_error,
            throw_on_error=True
        )

    environment_type_mismatch_error = config.Environment(
        sources={}, context=config.Context('default', {'string_arg': 1})
    )

    with pytest.raises(DagsterTypeError, message='Argument mismatch in context default'):
        execute_pipeline(
            with_argful_context_pipeline,
            environment=environment_type_mismatch_error,
            throw_on_error=True
        )
