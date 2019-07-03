import pytest

from dagster import (
    Dict,
    Field,
    DagsterInvalidConfigError,
    PipelineDefinition,
    SolidDefinition,
    String,
    execute_pipeline,
)


def test_basic_solid_with_config():
    did_get = {}

    def _t_fn(context, _inputs):
        did_get['yep'] = context.solid_config

    solid = SolidDefinition(
        name='solid_with_context',
        input_defs=[],
        output_defs=[],
        config_field=Field(Dict({'some_config': Field(String)})),
        compute_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solid_defs=[solid])

    execute_pipeline(
        pipeline, {'solids': {'solid_with_context': {'config': {'some_config': 'foo'}}}}
    )

    assert 'yep' in did_get
    assert 'some_config' in did_get['yep']


def test_config_arg_mismatch():
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid = SolidDefinition(
        name='solid_with_context',
        input_defs=[],
        output_defs=[],
        config_field=Field(Dict({'some_config': Field(String)})),
        compute_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solid_defs=[solid])

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline, {'solids': {'solid_with_context': {'config': {'some_config': 1}}}}
        )


def test_solid_not_found():
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid = SolidDefinition(name='find_me_solid', input_defs=[], output_defs=[], compute_fn=_t_fn)

    pipeline = PipelineDefinition(solid_defs=[solid])

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(pipeline, {'solids': {'not_found': {'config': {'some_config': 1}}}})


def test_config_for_no_config():
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid_def = SolidDefinition(
        name='no_config_solid', input_defs=[], output_defs=[], compute_fn=_t_fn
    )

    pipeline = PipelineDefinition(solid_defs=[solid_def])

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(pipeline, {'solids': {'no_config_solid': {'config': {'some_config': 1}}}})
