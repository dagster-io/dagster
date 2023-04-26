from typing import Sequence

import pytest
from dagster import (
    DagsterEventType,
    DagsterInvariantViolationError,
    ExpectationResult,
    GraphDefinition,
    op,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.execution_result import ExecutionResult


def expt_results_for_compute_step(
    result: ExecutionResult, node_name: str
) -> Sequence[DagsterEvent]:
    return [
        compute_step_event
        for compute_step_event in result.events_for_node(node_name)
        if compute_step_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT
    ]


def test_successful_expectation_in_compute_step():
    @op(out={})
    def success_expectation_op(_context):
        yield ExpectationResult(success=True, description="This is always true.")

    job_def = GraphDefinition(
        name="success_expectation_in_compute_pipeline",
        node_defs=[success_expectation_op],
    ).to_job()

    result = job_def.execute_in_process()

    assert result
    assert result.success

    expt_results = expt_results_for_compute_step(result, "success_expectation_op")

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert expt_result.event_specific_data.expectation_result.success
    assert expt_result.event_specific_data.expectation_result.description == "This is always true."


def test_failed_expectation_in_compute_step():
    @op(out={})
    def failure_expectation_op(_context):
        yield ExpectationResult(success=False, description="This is always false.")

    job_def = GraphDefinition(
        name="failure_expectation_in_compute_pipeline",
        node_defs=[failure_expectation_op],
    ).to_job()

    result = job_def.execute_in_process()

    assert result
    assert result.success
    expt_results = expt_results_for_compute_step(result, "failure_expectation_op")

    assert len(expt_results) == 1
    expt_result = expt_results[0]
    assert not expt_result.event_specific_data.expectation_result.success
    assert expt_result.event_specific_data.expectation_result.description == "This is always false."


def test_return_expectation_failure():
    @op
    def return_expectation_failure(_context):
        return ExpectationResult(success=True, description="This is always true.")

    job_def = GraphDefinition(
        name="success_expectation_in_compute_pipeline",
        node_defs=[return_expectation_failure],
    ).to_job()

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "If you are returning an AssetMaterialization or an ExpectationResult from op you must"
            " yield them directly"
        ),
    ):
        job_def.execute_in_process()
