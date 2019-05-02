import pytest

from dagster import (
    DagsterEventType,
    DagsterInvariantViolationError,
    ExpectationResult,
    PipelineDefinition,
    execute_pipeline,
    solid,
)


def expectation_results_for_solid_transform(result, solid_name):
    solid_result = result.result_for_solid(solid_name)
    return [
        t_event
        for t_event in solid_result.transforms
        if t_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT
    ]


def test_successful_expectation_in_transform():
    @solid(outputs=[])
    def success_expectation_solid(_context):
        yield ExpectationResult(success=True, message='This is always true.')

    pipeline_def = PipelineDefinition(
        name='success_expectation_in_transform_pipeline', solids=[success_expectation_solid]
    )

    result = execute_pipeline(pipeline_def)

    assert result
    assert result.success

    expt_results = expectation_results_for_solid_transform(result, 'success_expectation_solid')

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert expt_result.event_specific_data.expectation_result.success
    assert expt_result.event_specific_data.expectation_result.message == 'This is always true.'


def test_failed_expectation_in_transform():
    @solid(outputs=[])
    def failure_expectation_solid(_context):
        yield ExpectationResult(success=False, message='This is always false.')

    pipeline_def = PipelineDefinition(
        name='failure_expectation_in_transform_pipeline', solids=[failure_expectation_solid]
    )

    result = execute_pipeline(pipeline_def)

    assert result
    assert result.success
    expt_results = expectation_results_for_solid_transform(result, 'failure_expectation_solid')

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert not expt_result.event_specific_data.expectation_result.success
    assert expt_result.event_specific_data.expectation_result.message == 'This is always false.'


def test_return_expectation_failure():
    @solid(outputs=[])
    def return_expectation_failure(_context):
        return ExpectationResult(success=True, message='This is always true.')

    pipeline_def = PipelineDefinition(
        name='success_expectation_in_transform_pipeline', solids=[return_expectation_failure]
    )

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(pipeline_def)

    assert str(exc_info.value) == (
        'Error in solid return_expectation_failure: If you are returning '
        'a Materialization or an ExpectationResult from solid you must yield '
        'them to avoid ambiguity with an implied result from returning a value.'
    )
