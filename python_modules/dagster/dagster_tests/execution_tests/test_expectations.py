import pytest

from dagster import (
    op,
    DagsterEventType,
    DagsterInvariantViolationError,
    ExpectationResult,
)
from dagster._legacy import PipelineDefinition, execute_pipeline, solid


def expt_results_for_compute_step(result, solid_name):
    solid_result = result.result_for_solid(solid_name)
    return [
        compute_step_event
        for compute_step_event in solid_result.compute_step_events
        if compute_step_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT
    ]


def test_successful_expectation_in_compute_step():
    @op(out={})
    def success_expectation_op(_context):
        yield ExpectationResult(success=True, description="This is always true.")

    pipeline_def = PipelineDefinition(
        name="success_expectation_in_compute_pipeline",
        solid_defs=[success_expectation_op],
    )

    result = execute_pipeline(pipeline_def)

    assert result
    assert result.success

    expt_results = expt_results_for_compute_step(result, "success_expectation_op")

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert expt_result.event_specific_data.expectation_result.success
    assert (
        expt_result.event_specific_data.expectation_result.description
        == "This is always true."
    )


def test_failed_expectation_in_compute_step():
    @op(out={})
    def failure_expectation_op(_context):
        yield ExpectationResult(success=False, description="This is always false.")

    pipeline_def = PipelineDefinition(
        name="failure_expectation_in_compute_pipeline",
        solid_defs=[failure_expectation_op],
    )

    result = execute_pipeline(pipeline_def)

    assert result
    assert result.success
    expt_results = expt_results_for_compute_step(result, "failure_expectation_op")

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert not expt_result.event_specific_data.expectation_result.success
    assert (
        expt_result.event_specific_data.expectation_result.description
        == "This is always false."
    )


def test_return_expectation_failure():
    @op(out={})
    def return_expectation_failure(_context):
        return ExpectationResult(success=True, description="This is always true.")

    pipeline_def = PipelineDefinition(
        name="success_expectation_in_compute_pipeline",
        solid_defs=[return_expectation_failure],
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match="If you are returning an AssetMaterialization or an ExpectationResult from solid you must yield them directly",
    ):
        execute_pipeline(pipeline_def)
