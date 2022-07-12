import pytest

import dagster._check as check
from dagster import OpExecutionContext, execute_pipeline, job, op, pipeline
from dagster.core.definitions.job_definition import JobDefinition
from dagster.core.definitions.op_definition import OpDefinition
from dagster.core.definitions.pipeline_definition import PipelineDefinition
from dagster.core.definitions.solid_definition import SolidDefinition
from dagster.core.execution.context.compute import SolidExecutionContext
from dagster.core.storage.pipeline_run import DagsterRun, PipelineRun
from dagster.legacy import solid


def test_op_execution_context():
    @op
    def ctx_op(context: OpExecutionContext):
        check.inst(context.run, DagsterRun)
        assert context.job_name == "foo"
        assert context.job_def.name == "foo"
        check.inst(context.job_def, JobDefinition)
        assert context.op_config is None
        check.inst(context.op_def, OpDefinition)

        check.inst(context.pipeline_run, PipelineRun)
        assert context.pipeline_name == "foo"
        assert context.pipeline_def.name == "foo"
        check.inst(context.pipeline_def, PipelineDefinition)
        assert context.solid_config is None
        check.inst(context.solid_def, SolidDefinition)

    @job
    def foo():
        ctx_op()

    assert foo.execute_in_process().success


def test_solid_execution_context():
    @solid
    def ctx_solid(context: SolidExecutionContext):
        check.inst(context.run, DagsterRun)
        assert context.job_name == "foo"

        with pytest.raises(Exception):
            context.job_def  # pylint: disable=pointless-statement

        assert context.op_config is None

        with pytest.raises(Exception):
            context.op_def  # pylint: disable=pointless-statement

        check.inst(context.pipeline_run, PipelineRun)
        assert context.pipeline_name == "foo"
        assert context.pipeline_def.name == "foo"
        check.inst(context.pipeline_def, PipelineDefinition)
        assert context.solid_config is None
        check.inst(context.solid_def, SolidDefinition)

    @pipeline
    def foo():
        ctx_solid()

    assert execute_pipeline(foo).success
