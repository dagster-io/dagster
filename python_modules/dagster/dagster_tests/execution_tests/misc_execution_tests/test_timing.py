import sys
import time

import pytest
from dagster import GraphDefinition, In, Output, input_manager, op


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_before_yield():
    @op
    def before_yield_op(_context):
        time.sleep(0.01)
        yield Output(None)

    job_def = GraphDefinition(node_defs=[before_yield_op], name="test").to_job()
    result = job_def.execute_in_process()
    success_event = result.get_step_success_events()[0]

    assert success_event.event_specific_data.duration_ms >= 10.0  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_after_yield():
    @op
    def after_yield_op(_context):
        yield Output(None)
        time.sleep(0.01)

    job_def = GraphDefinition(node_defs=[after_yield_op], name="test").to_job()
    result = job_def.execute_in_process()
    success_event = result.get_step_success_events()[0]
    assert success_event.event_specific_data.duration_ms >= 10.0  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_direct_return():
    @op
    def direct_return_op(_context):
        time.sleep(0.01)
        return None

    job_def = GraphDefinition(node_defs=[direct_return_op], name="test").to_job()
    result = job_def.execute_in_process()
    success_event = result.get_step_success_events()[0]
    assert success_event.event_specific_data.duration_ms >= 10.0  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_include_input_loading():
    @op(ins={"in1": In(input_manager_key="foo")})
    def direct_return_op(in1):
        return None

    @input_manager
    def my_input_manager():
        time.sleep(0.01)
        return None

    job_def = GraphDefinition(node_defs=[direct_return_op], name="test").to_job(
        resource_defs={"foo": my_input_manager}
    )
    result = job_def.execute_in_process()
    success_event = result.get_step_success_events()[0]
    assert success_event.event_specific_data.duration_ms >= 10.0  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
