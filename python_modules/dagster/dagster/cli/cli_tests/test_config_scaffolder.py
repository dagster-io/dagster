from dagster import (
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    types,
)

from dagster.core.config_types import EnvironmentConfigType

from dagster.cli.config_scaffolder import (
    scaffold_pipeline_config,
    scaffold_type,
)


def fail_me():
    return check.failed('Should not call')


def test_scalars():
    assert scaffold_type(types.Int) == 0
    assert scaffold_type(types.String) == ''
    assert scaffold_type(types.Path) == 'path/to/something'
    assert scaffold_type(types.Bool) is True
    assert scaffold_type(types.PythonDict) == {}
    assert scaffold_type(types.Any) == 'AnyType'


def test_basic_solids_config():
    pipeline_def = PipelineDefinition(
        name='BasicSolidsConfigPipeline',
        solids=[
            SolidDefinition(
                name='required_field_solid',
                inputs=[],
                outputs=[],
                config_field=Field(types.Dict(fields={'required_int': types.Field(types.Int)})),
                transform_fn=lambda *_args: fail_me(),
            )
        ]
    )

    env_config_type = EnvironmentConfigType(pipeline_def)

    assert env_config_type.field_dict['solids'].is_optional is False
    solids_config_type = env_config_type.field_dict['solids'].dagster_type
    assert solids_config_type.field_dict['required_field_solid'].is_optional is False
    required_solid_config_type = solids_config_type.field_dict['required_field_solid'].dagster_type
    assert required_solid_config_type.field_dict['config'].is_optional is False

    context_config_type = env_config_type.field_dict['context'].dagster_type

    assert 'default' in context_config_type.field_dict
    assert context_config_type.field_dict['default'].is_optional

    default_context_config_type = context_config_type.field_dict['default'].dagster_type

    assert set(default_context_config_type.field_dict.keys()) == set(['config', 'resources'])

    default_context_user_config_type = default_context_config_type.field_dict['config'].dagster_type

    assert set(default_context_user_config_type.field_dict.keys()) == set(['log_level'])

    assert scaffold_pipeline_config(
        pipeline_def,
        skip_optional=False,
    ) == {
        'context': {
            'default': {
                'config': {
                    'log_level': '',
                },
                'resources': {},
            },
        },
        'solids': {
            'required_field_solid': {
                'config': {
                    'required_int': 0,
                },
            },
        },
        'execution': {
            'serialize_intermediates': True,
        },
        'expectations': {
            'evaluate': True,
        },
    }


def test_two_contexts():
    pipeline_def = PipelineDefinition(
        name='TwoContextsPipeline',
        solids=[],
        context_definitions={
            'context_one':
            PipelineContextDefinition(
                context_fn=lambda *args: fail_me(),
                config_field=Field(types.Dict({
                    'context_one_field': types.Field(types.String)
                })),
            ),
            'context_two':
            PipelineContextDefinition(
                context_fn=lambda *args: fail_me(),
                config_field=Field(types.Dict({
                    'context_two_field': types.Field(types.Int)
                })),
            ),
        },
    )

    assert scaffold_pipeline_config(pipeline_def) == {'context': {}}

    assert scaffold_pipeline_config(
        pipeline_def,
        skip_optional=False,
    ) == {
        'context': {
            'context_one': {
                'config': {
                    'context_one_field': '',
                },
                'resources': {},
            },
            'context_two': {
                'config': {
                    'context_two_field': 0,
                },
                'resources': {},
            },
        },
        'solids': {},
        'execution': {
            'serialize_intermediates': True,
        },
        'expectations': {
            'evaluate': True,
        },
    }
