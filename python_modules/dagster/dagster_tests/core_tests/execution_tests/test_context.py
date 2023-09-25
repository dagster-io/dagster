import warnings

import dagster._check as check
import pytest
from dagster import AssetExecutionContext, OpExecutionContext, job, op
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.storage.dagster_run import DagsterRun


def test_op_execution_context():
    @op
    def ctx_op(context: OpExecutionContext):
        check.inst(context.run, DagsterRun)
        assert context.job_name == "foo"
        assert context.job_def.name == "foo"
        check.inst(context.job_def, JobDefinition)
        assert context.op_config is None
        check.inst(context.op_def, OpDefinition)

    @job
    def foo():
        ctx_op()

    assert foo.execute_in_process().success


def test_instance_check():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    warnings.filterwarnings("error")

    @op
    def test_op_context_instance_check(context: OpExecutionContext):
        step_context = context._step_execution_context  # noqa: SLF001
        asset_context = AssetExecutionContext(step_execution_context=step_context)
        op_context = OpExecutionContext(step_execution_context=step_context)
        with pytest.raises(DeprecationWarning):
            isinstance(asset_context, OpExecutionContext)
        assert isinstance(op_context, OpExecutionContext)

    @job
    def test_isinstance():
        test_op_context_instance_check()

    test_isinstance.execute_in_process()
