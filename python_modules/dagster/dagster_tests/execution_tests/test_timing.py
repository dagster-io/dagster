import sys
import time

import pytest

from dagster import Output, op
from dagster._legacy import PipelineDefinition, execute_pipeline


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_before_yield():
    @op
    def before_yield_op(_context):
        time.sleep(0.01)
        yield Output(None)

    pipeline_def = PipelineDefinition(solid_defs=[before_yield_op], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("before_yield_op").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_after_yield():
    @op
    def after_yield_op(_context):
        yield Output(None)
        time.sleep(0.01)

    pipeline_def = PipelineDefinition(solid_defs=[after_yield_op], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("after_yield_op").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_direct_return():
    @op
    def direct_return_op(_context):
        time.sleep(0.01)
        return None

    pipeline_def = PipelineDefinition(solid_defs=[direct_return_op], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("direct_return_op").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0
