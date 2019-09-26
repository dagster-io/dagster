import pytest

from dagster import DagsterInvalidConfigError, Field, String, execute_pipeline, pipeline, solid


def test_basic_solid_with_config():
    did_get = {}

    @solid(
        name='solid_with_context',
        input_defs=[],
        output_defs=[],
        config={'some_config': Field(String)},
    )
    def solid_with_context(context):
        did_get['yep'] = context.solid_config

    @pipeline
    def pipeline_def():
        solid_with_context()

    execute_pipeline(
        pipeline_def, {'solids': {'solid_with_context': {'config': {'some_config': 'foo'}}}}
    )

    assert 'yep' in did_get
    assert 'some_config' in did_get['yep']


def test_config_arg_mismatch():
    def _t_fn(*_args):
        raise Exception('should not reach')

    @solid(
        name='solid_with_context',
        input_defs=[],
        output_defs=[],
        config={'some_config': Field(String)},
    )
    def solid_with_context(context):
        raise Exception('should not reach')

    @pipeline
    def pipeline_def():
        solid_with_context()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def, {'solids': {'solid_with_context': {'config': {'some_config': 1}}}}
        )


def test_solid_not_found():
    @solid(name='find_me_solid', input_defs=[], output_defs=[])
    def find_me_solid(_):
        raise Exception('should not reach')

    @pipeline
    def pipeline_def():
        find_me_solid()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(pipeline_def, {'solids': {'not_found': {'config': {'some_config': 1}}}})


def test_config_for_no_config():
    @solid(name='no_config_solid', input_defs=[], output_defs=[])
    def no_config_solid(_):
        raise Exception('should not reach')

    @pipeline
    def pipeline_def():
        return no_config_solid()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def, {'solids': {'no_config_solid': {'config': {'some_config': 1}}}}
        )
