import pytest

from dagster import (
    DagsterInvariantViolationError,
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    ReentrantInfo,
    execute_pipeline,
    solid,
)


def test_injected_run_id():
    run_id = 'kdjfkdjfkd'
    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[])
    result = execute_pipeline(pipeline_def, reentrant_info=ReentrantInfo(run_id=run_id))

    assert result.success
    assert result.context.run_id == run_id


def test_injected_context_stack():
    called = {}

    @solid
    def check_context_stack(info):
        assert info.context.get_context_value('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solids=[check_context_stack])
    result = execute_pipeline(
        pipeline_def, reentrant_info=ReentrantInfo(context_stack={'foo': 'bar'})
    )

    assert result.success
    assert called['yup']


def test_user_injected_context_stack():
    called = {}

    @solid
    def check_context_stack(info):
        assert info.context.get_context_value('foo') == 'bar'
        assert info.context.get_context_value('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_info):
        return ExecutionContext(context_stack={'quux': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_context_stack],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    result = execute_pipeline(
        pipeline_def, reentrant_info=ReentrantInfo(context_stack={'foo': 'bar'})
    )

    assert result.success
    assert called['yup']


def test_user_injected_context_stack_collision():
    called = {}

    @solid
    def check_context_stack(info):
        assert info.context.get_context_value('foo') == 'bar'
        assert info.context.get_context_value('quux') == 'baaz'
        called['yup'] = True

    def _create_context(_info):
        return ExecutionContext(context_stack={'foo': 'baaz'})

    pipeline_def = PipelineDefinition(
        name='injected_run_id',
        solids=[check_context_stack],
        context_definitions={'default': PipelineContextDefinition(context_fn=_create_context)},
    )

    with pytest.raises(DagsterInvariantViolationError, match='You have specified'):
        execute_pipeline(pipeline_def, reentrant_info=ReentrantInfo(context_stack={'foo': 'bar'}))
