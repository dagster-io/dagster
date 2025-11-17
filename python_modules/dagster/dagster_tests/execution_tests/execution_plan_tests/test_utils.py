from contextlib import contextmanager

import dagster as dg
import pytest
from dagster._core.errors import DagsterExecutionStepExecutionError
from dagster._core.execution.plan.utils import (
    RetryRequestedFromPolicy,
    build_resources_for_manager,
    op_execution_error_boundary,
)


@contextmanager
def _job_context(job_def: dg.JobDefinition, step_context_factory, step_key: str | None = None):
    with step_context_factory(job_def, step_key=step_key) as step_context:
        yield step_context


def test_build_resources_for_manager_returns_required_resources(step_context_factory):
    @dg.resource
    def base_resource():
        return "base"

    @dg.io_manager(required_resource_keys={"base_resource"})
    def dependent_io_manager(_context):
        class Manager(dg.IOManager):
            def handle_output(self, context, obj):
                pass

            def load_input(self, context):
                pass

        return Manager()

    @dg.op(out=dg.Out(io_manager_key="io_manager"))
    def emit() -> int:
        return 1

    @dg.job(resource_defs={"base_resource": base_resource, "io_manager": dependent_io_manager})
    def job_def():
        emit()

    with _job_context(job_def, step_context_factory) as step_context:
        resources = build_resources_for_manager("io_manager", step_context)

    assert hasattr(resources, "base_resource")
    assert resources.base_resource == "base"


def test_op_execution_error_boundary_wraps_generic_exception(simple_step_context):
    with pytest.raises(DagsterExecutionStepExecutionError):
        with op_execution_error_boundary(
            DagsterExecutionStepExecutionError,
            msg_fn=lambda: "Error occurred",
            step_context=simple_step_context,
            step_key=simple_step_context.step.key,
            op_name=simple_step_context.op.name,
            op_def_name=simple_step_context.op_def.name,
        ):
            raise Exception("boom")


def test_op_execution_error_boundary_uses_retry_policy(step_context_factory):
    @dg.op(retry_policy=dg.RetryPolicy(max_retries=3))
    def flaky():
        return 1

    @dg.job
    def job_def():
        flaky()

    with _job_context(job_def, step_context_factory) as step_context:
        with pytest.raises(RetryRequestedFromPolicy) as excinfo:
            with op_execution_error_boundary(
                DagsterExecutionStepExecutionError,
                msg_fn=lambda: "msg",
                step_context=step_context,
                step_key=step_context.step.key,
                op_name=step_context.op.name,
                op_def_name=step_context.op_def.name,
            ):
                raise Exception("boom")

    assert excinfo.value.max_retries == 3
    assert excinfo.value.seconds_to_wait is not None
    assert excinfo.value.seconds_to_wait >= 0
