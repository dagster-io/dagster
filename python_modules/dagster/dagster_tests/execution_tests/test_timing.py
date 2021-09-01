import sys
import time

import pytest
from dagster import Output, PipelineDefinition, execute_pipeline, solid


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_before_yield():
    @solid
    def before_yield_solid(_context):
        time.sleep(0.01)
        yield Output(None)

    pipeline_def = PipelineDefinition(solid_defs=[before_yield_solid], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("before_yield_solid").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_after_yield():
    @solid
    def after_yield_solid(_context):
        yield Output(None)
        time.sleep(0.01)

    pipeline_def = PipelineDefinition(solid_defs=[after_yield_solid], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("after_yield_solid").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0


@pytest.mark.skipif(
    sys.platform == "win32", reason="https://github.com/dagster-io/dagster/issues/1421"
)
def test_event_timing_direct_return():
    @solid
    def direct_return_solid(_context):
        time.sleep(0.01)
        return None

    pipeline_def = PipelineDefinition(solid_defs=[direct_return_solid], name="test")
    pipeline_result = execute_pipeline(pipeline_def)
    success_event = pipeline_result.result_for_solid("direct_return_solid").get_step_success_event()
    assert success_event.event_specific_data.duration_ms >= 10.0
