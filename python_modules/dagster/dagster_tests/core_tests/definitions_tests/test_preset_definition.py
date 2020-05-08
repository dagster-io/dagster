import re

import pytest

from dagster import (
    Bool,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    check,
    execute_pipeline,
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
            PresetDefinition.from_files(
                'passing_overide_to_fail',
                environment_files=[file_relative_path(__file__, 'pass_env.yaml')],
                solid_subset=['can_fail'],
            ).with_additional_config({'solids': {'can_fail': {'config': {'error': True}}}}),
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
            PresetDefinition('subset', solid_subset=['can_fail'],),
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

    assert execute_pipeline(pipeline, preset='passing').success

    assert execute_pipeline(pipeline, preset='passing_direct_dict').success
    assert execute_pipeline(pipeline, preset='failing_1', raise_on_error=False).success == False

    assert execute_pipeline(pipeline, preset='failing_2', raise_on_error=False).success == False

    with pytest.raises(DagsterInvariantViolationError, match='Could not find preset'):
        execute_pipeline(pipeline, preset='not_failing', raise_on_error=False)

    assert (
        execute_pipeline(pipeline, preset='passing_overide_to_fail', raise_on_error=False).success
        == False
    )

    assert execute_pipeline(
        pipeline,
        preset='passing',
        environment_dict={'solids': {'can_fail': {'config': {'error': False}}}},
    ).success

    with pytest.raises(
        check.CheckError,
        match=re.escape(
            'The environment set in preset \'passing\' does not agree with the environment passed '
            'in the `environment_dict` argument.'
        ),
    ):
        execute_pipeline(
            pipeline,
            preset='passing',
            environment_dict={'solids': {'can_fail': {'config': {'error': True}}}},
        )

    assert execute_pipeline(
        pipeline,
        preset='subset',
        environment_dict={'solids': {'can_fail': {'config': {'error': False}}}},
    ).success


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


def test_conflicting_preset():
    @lambda_solid
    def lil_solid():
        return ';)'

    with pytest.raises(
        DagsterInvalidDefinitionError, match='Two PresetDefinitions seen with the name'
    ):
        PipelineDefinition(
            name="preset_modes",
            solid_defs=[lil_solid],
            mode_defs=[ModeDefinition(name="mode_a")],
            preset_defs=[
                PresetDefinition(name="preset_a", mode="mode_a"),
                PresetDefinition(name="preset_a", mode="mode_a"),
            ],
        )


def test_from_yaml_strings():
    a = '''
foo:
  bar: 1
baz: 3
'''
    b = '''
foo:
  one: "one"
other: 4
'''
    c = '''
final: "result"
'''
    preset = PresetDefinition.from_yaml_strings('passing', [a, b, c])
    assert preset.environment_dict == {
        'foo': {'bar': 1, 'one': 'one'},
        'baz': 3,
        'other': 4,
        'final': 'result',
    }
    with pytest.raises(
        DagsterInvariantViolationError, match='Encountered error attempting to parse yaml'
    ):
        PresetDefinition.from_yaml_strings('failing', ['--- `'])

    res = PresetDefinition.from_yaml_strings('empty')
    assert res == PresetDefinition(
        name='empty', environment_dict={}, solid_subset=None, mode='default'
    )


def test_from_pkg_resources():
    good = ('dagster_tests.core_tests.definitions_tests', 'pass_env.yaml')
    res = PresetDefinition.from_pkg_resources('pass', [good])
    assert res.environment_dict == {'solids': {'can_fail': {'config': {'error': False}}}}

    bad_defs = [
        ('dagster_tests.core_tests.definitions_tests', 'does_not_exist.yaml'),
        ('dagster_tests.core_tests.definitions_tests', 'bad_file_binary.yaml'),
        ('dagster_tests.core_tests.does_not_exist', 'some_file.yaml'),
    ]

    for bad_def in bad_defs:
        with pytest.raises(
            DagsterInvariantViolationError, match='Encountered error attempting to parse yaml',
        ):
            PresetDefinition.from_pkg_resources('bad_def', [bad_def])
