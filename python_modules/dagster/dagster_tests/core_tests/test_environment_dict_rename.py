import re

import pytest
from dagster import PipelineRun, execute_pipeline, execute_pipeline_iterator, pipeline, solid


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    noop_solid()


def test_no_warnings_execute_pipeline():
    # flush out unrelated warnings
    assert execute_pipeline(noop_pipeline).success

    with pytest.warns(None) as record:
        assert execute_pipeline(noop_pipeline).success

    assert len(record) == 0

    with pytest.warns(None) as record:
        assert execute_pipeline(noop_pipeline, run_config={}).success

    assert len(record) == 0


def test_no_warnings_execute_pipeline_iterator():
    # flush out unrelated warnings
    list(execute_pipeline_iterator(noop_pipeline))

    with pytest.warns(None) as record:
        list(execute_pipeline_iterator(noop_pipeline))

    assert len(record) == 0

    with pytest.warns(None) as record:
        list(execute_pipeline_iterator(noop_pipeline, run_config={}))

    assert len(record) == 0
