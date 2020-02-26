import pytest

from dagster import (
    Bool,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    execute_pipeline_with_preset,
    lambda_solid,
    solid,
)
from dagster.utils import file_relative_path


def test_presets():
    @solid(config={'error': Bool})
    def can_fail(context):
        if context.solid_config['error']:
            raise Exception('I did an error')
        return 'cool'

    @lambda_solid
    def always_fail():
        raise Exception('I always do this')

    pipeline = PipelineDefinition(
        name='simple',
        solid_defs=[can_fail, always_fail],
        preset_defs=[
            PresetDefinition.from_files(
                'passing',
                environment_files=[file_relative_path(__file__, 'pass_env.yaml')],
                solid_subset=['can_fail'],
            ),
            PresetDefinition(
                'passing_direct_dict',
                environment_dict={'solids': {'can_fail': {'config': {'error': False}}}},
                solid_subset=['can_fail'],
            ),
            PresetDefinition.from_files(
                'failing_1',
                environment_files=[file_relative_path(__file__, 'fail_env.yaml')],
                solid_subset=['can_fail'],
            ),
            PresetDefinition.from_files(
                'failing_2', environment_files=[file_relative_path(__file__, 'pass_env.yaml')]
            ),
        ],
    )

    with pytest.raises(DagsterInvalidDefinitionError):
        PresetDefinition.from_files(
            'invalid_1', environment_files=[file_relative_path(__file__, 'not_a_file.yaml')]
        )

    with pytest.raises(DagsterInvariantViolationError):
        PresetDefinition.from_files(
            'invalid_2',
            environment_files=[file_relative_path(__file__, 'test_repository_definition.py')],
        )

    assert execute_pipeline_with_preset(pipeline, 'passing').success

    assert execute_pipeline_with_preset(pipeline, 'passing_direct_dict').success

    with pytest.raises(Exception):
        execute_pipeline_with_preset(pipeline, 'failing_1')

    with pytest.raises(Exception):
        execute_pipeline_with_preset(pipeline, 'failing_2')

    with pytest.raises(Exception, match="Could not find preset"):
        execute_pipeline_with_preset(pipeline, 'not_failing')


def test_invalid_preset():
    @lambda_solid
    def lil_solid():
        return ';)'

    with pytest.raises(DagsterInvalidDefinitionError, match='mode "mode_b" which is not defined'):
        PipelineDefinition(
            name="preset_modes",
            solid_defs=[lil_solid],
            mode_defs=[ModeDefinition(name="mode_a")],
            preset_defs=[PresetDefinition(name="preset_b", mode="mode_b")],
        )
