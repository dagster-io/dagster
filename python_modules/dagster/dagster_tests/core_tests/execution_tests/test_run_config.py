import time
import uuid

import pytest

from dagster import solid, PipelineDefinition, execute_pipeline, RunConfig
from dagster.core.execution.config import EXECUTION_TIME_KEY

EPS = 0.001


def test_default_run_id():
    called = {}

    @solid
    def check_run_id(context):
        called['yes'] = True
        assert uuid.UUID(context.run_id)
        called['run_id'] = context.run_id

    pipeline = PipelineDefinition(solid_defs=[check_run_id])

    result = execute_pipeline(pipeline)
    assert result.run_id == called['run_id']
    assert called['yes']


def test_provided_run_id():
    called = {}

    @solid
    def check_run_id(context):
        called['yes'] = True
        assert context.run_id == 'given'

    pipeline = PipelineDefinition(solid_defs=[check_run_id])

    result = execute_pipeline(pipeline, run_config=RunConfig(run_id='given'))
    assert result.run_id == 'given'

    assert called['yes']


def test_injected_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solid_defs=[check_tags])
    result = execute_pipeline(pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}))

    assert result.success
    assert called['yup']


def test_execution_time():
    # Should be cast back to string
    now = time.time()
    now_str = '%f' % now
    rc = RunConfig(tags={EXECUTION_TIME_KEY: now_str})
    assert abs(rc.tags[EXECUTION_TIME_KEY] - now) < EPS

    # Must be castable to float
    with pytest.raises(ValueError) as exc_info:
        rc = RunConfig(tags={EXECUTION_TIME_KEY: 'nope'})
    assert 'could not convert string to float' in str(exc_info.value)
