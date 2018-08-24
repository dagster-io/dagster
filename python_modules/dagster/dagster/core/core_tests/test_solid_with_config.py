import pytest

from dagster import (
    ArgumentDefinition,
    ConfigDefinition,
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
        name='with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition({
            'some_config': ArgumentDefinition(types.String)
        }),
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    execute_pipeline(
        pipeline,
        config.Environment(
            solids={'with_context': config.Solid(config_dict={'some_config': 'foo'})}
        ),
    )

    assert 'yep' in did_get
    assert 'some_config' in did_get['yep']


def test_config_arg_mismatch():
    def _t_fn(_context, _inputs, _config_dict):
        raise Exception('should not reach')

    solid = SolidDefinition(
        name='with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition({
            'some_config': ArgumentDefinition(types.String)
        }),
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    with pytest.raises(DagsterTypeError):
        execute_pipeline(
            pipeline,
            config.Environment(
                solids={'with_context': config.Solid(config_dict={'some_config': 1})}
            ),
        )
