import pytest

from dagster import (
    DagsterInvariantViolationError,
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    ExecutionMetadata,
    execute_pipeline,
    solid,
)


def test_injected_run_id():
    run_id = 'kdjfkdjfkd'
    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[])
    result = execute_pipeline(pipeline_def, execution_metadata=ExecutionMetadata(run_id=run_id))

    assert result.success
    assert result.context.run_id == run_id


def test_injected_tags():
    called = {}

    @solid
    def check_tags(info):
        assert info.context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[check_tags])
    result = execute_pipeline(
        pipeline_def, execution_metadata=ExecutionMetadata(tags={'foo': 'bar'})
    )

    assert result.success
    assert called['yup']


def test_user_injected_tags():
    called = {}

    @solid
    def check_tags(info):
        assert info.context.get_tag('foo') == 'bar'
        assert info.context.get_tag('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_info):
        return ExecutionContext(tags={'quux': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_tags],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    result = execute_pipeline(
        pipeline_def, execution_metadata=ExecutionMetadata(tags={'foo': 'bar'})
    )

    assert result.success
    assert called['yup']


def test_user_injected_tags_collision():
    called = {}

    @solid
    def check_tags(info):
        assert info.context.get_tag('foo') == 'bar'
        assert info.context.get_tag('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_info):
        return ExecutionContext(tags={'foo': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_tags],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    with pytest.raises(DagsterInvariantViolationError, match='You have specified'):
        execute_pipeline(pipeline_def, execution_metadata=ExecutionMetadata(tags={'foo': 'bar'}))
