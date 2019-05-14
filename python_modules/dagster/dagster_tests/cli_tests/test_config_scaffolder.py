from dagster import (
    Dict,
    Field,
    Int,
    ModeDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
    String,
    check,
)

from dagster.core.definitions import create_environment_type
from dagster.core.types import config
from dagster.cli.config_scaffolder import scaffold_pipeline_config, scaffold_type


def fail_me():
    return check.failed('Should not call')


def test_scalars():
    assert scaffold_type(config.Int.inst()) == 0
    assert scaffold_type(config.String.inst()) == ''
    assert scaffold_type(config.Path.inst()) == 'path/to/something'
    assert scaffold_type(config.Bool.inst()) is True
    assert scaffold_type(config.Any.inst()) == 'AnyType'


def test_basic_solids_config():
    pipeline_def = PipelineDefinition(
        name='BasicSolidsConfigPipeline',
        solids=[
            SolidDefinition(
                name='required_field_solid',
                inputs=[],
                outputs=[],
                config_field=Field(Dict(fields={'required_int': Field(Int)})),
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

    assert scaffold_pipeline_config(pipeline_def, skip_optional=False) == {
        'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
        'solids': {'required_field_solid': {'config': {'required_int': 0}}},
        'expectations': {'evaluate': True},
        'execution': {},
        'resources': {},
        'storage': {'filesystem': {'base_dir': ''}, 'in_memory': {}, 's3': {'s3_bucket': ''}},
    }


def dummy_resource(config_field):
    return ResourceDefinition(lambda: None, config_field)


def test_two_modes():
    pipeline_def = PipelineDefinition(
        name='TwoModePipelines',
        solids=[],
        mode_definitions=[
            ModeDefinition(
                'mode_one',
                resources={'value': dummy_resource(Field(Dict({'mode_one_field': Field(String)})))},
            ),
            ModeDefinition(
                'mode_two',
                resources={'value': dummy_resource(Field(Dict({'mode_two_field': Field(Int)})))},
            ),
        ],
    )

    assert scaffold_pipeline_config(pipeline_def, mode='mode_one') == {
        'resources': {'value': {'config': {'mode_one_field': ''}}}
    }

    assert scaffold_pipeline_config(pipeline_def, mode='mode_one', skip_optional=False) == {
        'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
        'solids': {},
        'expectations': {'evaluate': True},
        'storage': {'in_memory': {}, 'filesystem': {'base_dir': ''}, 's3': {'s3_bucket': ''}},
        'execution': {},
        'resources': {'value': {'config': {'mode_one_field': ''}}},
    }

    assert scaffold_pipeline_config(pipeline_def, mode='mode_two') == {
        'resources': {'value': {'config': {'mode_two_field': 0}}}
    }

    assert scaffold_pipeline_config(pipeline_def, mode='mode_two', skip_optional=False) == {
        'solids': {},
        'expectations': {'evaluate': True},
        'storage': {'in_memory': {}, 'filesystem': {'base_dir': ''}, 's3': {'s3_bucket': ''}},
        'execution': {},
        'resources': {'value': {'config': {'mode_two_field': 0}}},
        'loggers': {'console': {'config': {'log_level': '', 'name': ''}}},
    }
