from unittest.mock import Mock

from dagster import Nothing, ResourceDefinition, op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.input import In
from dagster_mlflow.hooks import _cleanup_on_success, end_mlflow_on_run_finished


def test_cleanup_on_success():
    # Given: - two mock ops
    mock_op_1 = Mock(name="op_1")
    mock_op_2 = Mock(name="op_2")

    # - a mock context containing a list of these two ops and a current op
    mock_context = Mock()
    step_execution_context = mock_context._step_execution_context  # noqa: SLF001
    step_execution_context.job_def.nodes_in_topological_order = [
        mock_op_1,
        mock_op_2,
    ]
    mock_context.op = mock_op_2

    # When: the cleanup function is called with the mock context
    _cleanup_on_success(mock_context)

    # Then:
    # - mlflow.end_run is called if op is the last op
    mock_context.resources.mlflow.end_run.assert_called_once()

    # - mlflow.end_run is not called when the op in the context is not the last op
    mock_context.reset_mock()
    mock_context.op = mock_op_1
    _cleanup_on_success(mock_context)
    mock_context.resources.mlflow.end_run.assert_not_called()


def test_end_mlflow_on_run_finished():
    mock_mlflow = Mock()

    @op
    def op1():
        pass

    @op(ins={"start": In(Nothing)})
    def op2():
        pass

    @end_mlflow_on_run_finished
    @job(resource_defs={"mlflow": ResourceDefinition.hardcoded_resource(mock_mlflow)})
    def mlf_job():
        op2(op1())

    mlf_job.execute_in_process()
    mock_mlflow.end_run.assert_called_once()
