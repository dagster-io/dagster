import pytest

from dagster import (
    ConfigDefinition,
    DagsterInvariantViolationError,
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

    def _t_fn(info, _inputs):
        did_get['yep'] = info.config

    solid = SolidDefinition(
        name='solid_with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition.config_dict('SomeConfig', {'some_config': Field(types.String)}),
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
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid = SolidDefinition(
        name='solid_with_context',
        inputs=[],
        outputs=[],
        config_def=ConfigDefinition.config_dict('SomeConfig', {'some_config': Field(types.String)}),
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


def test_solid_not_found():
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid = SolidDefinition(
        name='find_me_solid',
        inputs=[],
        outputs=[],
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid])

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline,
            config.Environment(solids={
                'not_found': config.Solid({
                    'some_config': 1,
                }),
            }),
        )


def test_config_for_no_config():
    def _t_fn(*_args):
        raise Exception('should not reach')

    solid_def = SolidDefinition(
        name='no_config_solid',
        inputs=[],
        outputs=[],
        transform_fn=_t_fn,
    )

    pipeline = PipelineDefinition(solids=[solid_def])

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Solid no_config_solid was provided {'some_config': 1} but does not take config",
    ):
        execute_pipeline(
            pipeline,
            config.Environment(solids={
                'no_config_solid': config.Solid({
                    'some_config': 1,
                }),
            }),
        )
