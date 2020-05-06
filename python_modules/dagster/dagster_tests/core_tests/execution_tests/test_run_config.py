import re
import uuid

import pytest

from dagster import PipelineDefinition, RunConfig, execute_pipeline, solid

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


def test_select_mode():
    called = {}

    @solid
    def check_run_id(context):
        called['yes'] = True
        assert uuid.UUID(context.run_id)
        called['run_id'] = context.run_id

    pipeline = PipelineDefinition(solid_defs=[check_run_id])

    with pytest.warns(
        UserWarning,
        match=re.escape(
            'In 0.8.0, the use of `run_config` to set pipeline mode and tags will be deprecated'
        ),
    ):
        result = execute_pipeline(pipeline, run_config=RunConfig(mode='default'))
    assert result.run_id == called['run_id']
    assert called['yes']


def test_injected_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solid_defs=[check_tags])
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'In 0.8.0, the use of `run_config` to set pipeline mode and tags will be deprecated'
        ),
    ):
        result = execute_pipeline(pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}))

    assert result.success
    assert called['yup']


def test_pipeline_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def_with_tags = PipelineDefinition(
        name='injected_run_id', solid_defs=[check_tags], tags={'foo': 'bar'}
    )
    result = execute_pipeline(pipeline_def_with_tags)
    assert result.success
    assert called['yup']

    called = {}
    pipeline_def_with_override_tags = PipelineDefinition(
        name='injected_run_id', solid_defs=[check_tags], tags={'foo': 'notbar'}
    )
    result = execute_pipeline(pipeline_def_with_override_tags, tags={'foo': 'bar'})
    assert result.success
    assert called['yup']


def test_overwrite_tags():
    called = {}

    @solid
    def check_tags(context):
        assert context.get_tag('foo') == 'baz'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='injected_run_id', solid_defs=[check_tags])
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'In 0.8.0, the use of `run_config` to set pipeline mode and tags will be deprecated'
        ),
    ):
        result = execute_pipeline(
            pipeline_def, run_config=RunConfig(tags={'foo': 'bar'}), tags={'foo': 'baz'}
        )

    assert result.success
    assert called['yup']
