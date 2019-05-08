from dagster import (
    Dict,
    Field,
    Int,
    PipelineContextDefinition,
    PipelineDefinition,
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
                transform_fn=lambda *_args: fail_me(),
            )
        ],
    )

    env_config_type = create_environment_type(pipeline_def)

    assert env_config_type.fields['solids'].is_optional is False
    solids_config_type = env_config_type.fields['solids'].config_type
    assert solids_config_type.fields['required_field_solid'].is_optional is False
    required_solid_config_type = solids_config_type.fields['required_field_solid'].config_type
    assert required_solid_config_type.fields['config'].is_optional is False

    context_config_type = env_config_type.fields['context'].config_type

    assert 'default' in context_config_type.fields
    assert context_config_type.fields['default'].is_optional

    default_context_config_type = context_config_type.fields['default'].config_type

    assert set(default_context_config_type.fields.keys()) == set(
        ['config', 'resources', 'persistence']
    )

    default_context_user_config_type = default_context_config_type.fields['config'].config_type

    assert set(default_context_user_config_type.fields.keys()) == set(['log_level'])

    assert scaffold_pipeline_config(pipeline_def, skip_optional=False) == {
        'context': {
            'default': {
                'config': {'log_level': 'DEBUG|INFO|WARNING|ERROR|CRITICAL'},
                'persistence': {'file': {}},
                'resources': {},
            }
        },
        'solids': {'required_field_solid': {'config': {'required_int': 0}}},
        'expectations': {'evaluate': True},
        'execution': {},
        'storage': {'filesystem': {'base_dir': ''}, 'in_memory': {}, 's3': {'s3_bucket': ''}},
    }


def test_two_contexts():
    pipeline_def = PipelineDefinition(
        name='TwoContextsPipeline',
        solids=[],
        context_definitions={
            'context_one': PipelineContextDefinition(
                context_fn=lambda *args: fail_me(),
                config_field=Field(Dict({'context_one_field': Field(String)})),
            ),
            'context_two': PipelineContextDefinition(
                context_fn=lambda *args: fail_me(),
                config_field=Field(Dict({'context_two_field': Field(Int)})),
            ),
        },
    )

    assert scaffold_pipeline_config(pipeline_def) == {'context': {}}

    assert scaffold_pipeline_config(pipeline_def, skip_optional=False) == {
        'context': {
            'context_one': {
                'config': {'context_one_field': ''},
                'persistence': {'file': {}},
                'resources': {},
            },
            'context_two': {
                'config': {'context_two_field': 0},
                'persistence': {'file': {}},
                'resources': {},
            },
        },
        'solids': {},
        'expectations': {'evaluate': True},
        'execution': {},
        'storage': {'filesystem': {'base_dir': ''}, 'in_memory': {}, 's3': {'s3_bucket': ''}},
    }
