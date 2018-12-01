from dagster import (RepositoryDefinition, PipelineDefinition, SolidDefinition, Field, types, ConfigField)
from dagster.dagster_examples.pandas_hello_world.pipeline import define_success_pipeline

def pipeline_list_config():
    value = [1, 2]
    called = {}

    def _test_config(info, _inputs):
        assert info.config == value
        called['yup'] = True

    return PipelineDefinition(
        name='pipeline_list_config',
        solids=[
            SolidDefinition(
                name='list_solid',
                inputs=[],
                outputs=[],
                config_field=Field(types.List(types.Int)),
                transform_fn=_test_config
            ),
        ],
    )

def pipeline_two_list_config():
    return PipelineDefinition(
        name='pipeline_two_list_config',
        solids=[
            SolidDefinition(
                name='two_list_solid',
                inputs=[],
                outputs=[],
                config_field=ConfigField.solid_config_dict(
                    'pipeline_two_list_config',
                    'two_list_solid',
                    {
                        'list_one': types.Field(types.List(types.Int)),
                        'list_two': types.Field(types.List(types.Int)),
                    },
                ),
                transform_fn=lambda *_args: None,
            ),
        ],
    )


def define_example_repository():
    return RepositoryDefinition(
        name='example_repo',
        pipeline_dict={
            'pandas_hello_world': define_success_pipeline,
            'pipeline_list_config': pipeline_list_config,
            'pipeline_two_list_config': pipeline_two_list_config},
    )
