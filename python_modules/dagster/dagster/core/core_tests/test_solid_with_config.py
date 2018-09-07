import pytest

from dagster import (
    ConfigDefinition,
    Field,
    PipelineDefinition,
    SolidDefinition,
    config,
    execute_pipeline,
    types,
)

from dagster.core.errors import DagsterTypeError


def test_basic_solid_with_config():
    did_get = {}

    def _t_fn(_context, _inputs, config_dict):
        did_get['yep'] = config_dict

    solid = SolidDefinition(
        name='solid_with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition.config_dict({
            'some_config': Field(types.String)
        }),
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    execute_pipeline(
        pipeline,
        config.Environment(solids={'solid_with_context': config.Solid({
            'some_config': 'foo'
        })}),
    )

    assert 'yep' in did_get
    assert 'some_config' in did_get['yep']


def test_config_arg_mismatch():
    def _t_fn(_context, _inputs, _config_dict):
        raise Exception('should not reach')

    solid = SolidDefinition(
        name='solid_with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition.config_dict({
            'some_config': Field(types.String)
        }),
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    with pytest.raises(DagsterTypeError):
        execute_pipeline(
            pipeline,
            config.Environment(solids={'solid_with_context': config.Solid({
                'some_config': 1
            })}),
        )
