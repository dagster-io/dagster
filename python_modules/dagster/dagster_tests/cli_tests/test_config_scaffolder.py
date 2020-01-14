from dagster import (
    Int,
    ModeDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
    String,
    check,
)
from dagster.cli.config_scaffolder import scaffold_pipeline_config, scaffold_type
from dagster.config import config_type
from dagster.core.definitions import create_environment_type


def fail_me():
    return check.failed('Should not call')


def test_scalars():
    assert scaffold_type(config_type.Int()) == 0
    assert scaffold_type(config_type.String()) == ''
    assert scaffold_type(config_type.Path()) == 'path/to/something'
    assert scaffold_type(config_type.Bool()) is True
    assert scaffold_type(config_type.Any()) == 'AnyType'


def test_basic_solids_config(snapshot):
    pipeline_def = PipelineDefinition(
        name='BasicSolidsConfigPipeline',
        solid_defs=[
            SolidDefinition(
                name='required_field_solid',
                input_defs=[],
                output_defs=[],
                config={'required_int': Int},
                compute_fn=lambda *_args: fail_me(),
            )
        ],
    )

    env_config_type = create_environment_type(pipeline_def)

    assert env_config_type.fields['solids'].is_optional is False
    solids_config_type = env_config_type.fields['solids'].config_type
    assert solids_config_type.fields['required_field_solid'].is_optional is False
    required_solid_config_type = solids_config_type.fields['required_field_solid'].config_type
    assert required_solid_config_type.fields['config'].is_optional is False

    assert set(env_config_type.fields['loggers'].config_type.fields.keys()) == set(['console'])

    console_logger_config_type = env_config_type.fields['loggers'].config_type.fields['console']

    assert set(console_logger_config_type.config_type.fields.keys()) == set(['config'])

    assert console_logger_config_type.config_type.fields['config'].is_optional

    console_logger_config_config_type = console_logger_config_type.config_type.fields[
        'config'
    ].config_type

    assert set(console_logger_config_config_type.fields.keys()) == set(['log_level', 'name'])

    snapshot.assert_match(scaffold_pipeline_config(pipeline_def, skip_optional=False))


def dummy_resource(config_field):
    return ResourceDefinition(lambda: None, config_field)


def test_two_modes(snapshot):
    pipeline_def = PipelineDefinition(
        name='TwoModePipelines',
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                'mode_one', resource_defs={'value': dummy_resource({'mode_one_field': String})},
            ),
            ModeDefinition(
                'mode_two', resource_defs={'value': dummy_resource({'mode_two_field': Int})},
            ),
        ],
    )

    snapshot.assert_match(scaffold_pipeline_config(pipeline_def, mode='mode_one'))

    snapshot.assert_match(
        scaffold_pipeline_config(pipeline_def, mode='mode_one', skip_optional=False)
    )

    snapshot.assert_match(scaffold_pipeline_config(pipeline_def, mode='mode_two'))

    snapshot.assert_match(
        scaffold_pipeline_config(pipeline_def, mode='mode_two', skip_optional=False)
    )
