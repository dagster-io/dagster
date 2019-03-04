import pytest

from dagster import (
    DagsterInvariantViolationError,
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    solid,
)


def test_injected_run_id():
    run_id = 'kdjfkdjfkd'
    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[])
    result = execute_pipeline(pipeline_def, run_config=RunConfig(run_id=run_id))

    assert result.success
    assert result.run_id == run_id


def test_injected_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[check_tags])
    result = execute_pipeline(pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}))

    assert result.success
    assert called['yup']


def test_user_injected_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        assert context.get_tag('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_context):
        return ExecutionContext(tags={'quux': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_tags],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    result = execute_pipeline(pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}))

    assert result.success
    assert called['yup']


def test_user_injected_tags_collision():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        assert context.get_tag('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_context):
        return ExecutionContext(tags={'foo': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_tags],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    with pytest.raises(DagsterInvariantViolationError, match='You have specified'):
        execute_pipeline(pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}))
