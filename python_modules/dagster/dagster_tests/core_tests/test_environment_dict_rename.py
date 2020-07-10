import re

import pytest

from dagster import PipelineRun, execute_pipeline, execute_pipeline_iterator, pipeline, solid


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    noop_solid()


def test_warnings_execute_pipeline():
    assert execute_pipeline(noop_pipeline).success

    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"environment_dict" is deprecated and will be removed in 0.9.0, '
            'use "run_config" instead.'
        ),
    ):
        assert execute_pipeline(noop_pipeline, environment_dict={}).success


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


def test_warnings_execute_pipeline_iterator():
    assert execute_pipeline(noop_pipeline).success

    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"environment_dict" is deprecated and will be removed in 0.9.0, '
            'use "run_config" instead.'
        ),
    ):
        list(execute_pipeline_iterator(noop_pipeline, environment_dict={}))


def test_pipeline_run():
    pipeline_run_one = PipelineRun(pipeline_name='foo', run_id='1', run_config={})
    assert pipeline_run_one.environment_dict == pipeline_run_one.run_config
    assert pipeline_run_one.environment_dict == {}

    pipeline_run_two = PipelineRun(pipeline_name='foo', run_id='1', run_config={})
    assert pipeline_run_two.environment_dict == pipeline_run_two.run_config
    assert pipeline_run_two.environment_dict == {}
