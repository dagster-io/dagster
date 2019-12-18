'''
Repository of test pipelines
'''

from dagster import (
    Int,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    resource,
    solid,
)
from dagster.utils import script_relative_path


def define_empty_pipeline():
    return PipelineDefinition(name='empty_pipeline', solid_defs=[])


def define_single_mode_pipeline():
    @solid
    def return_two(_context):
        return 2

    return PipelineDefinition(
        name='single_mode', solid_defs=[return_two], mode_defs=[ModeDefinition(name='the_mode')]
    )


def define_multi_mode_pipeline():
    @solid
    def return_three(_context):
        return 3

    return PipelineDefinition(
        name='multi_mode',
        solid_defs=[return_three],
        mode_defs=[ModeDefinition(name='mode_one'), ModeDefinition('mode_two')],
    )


def define_multi_mode_with_resources_pipeline():
    # API red alert. One has to wrap a type in Field because it is callable
    @resource(config=Int)
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config=Int)
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config={'num_one': Int, 'num_two': Int})
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config['num_one']
            + init_context.resource_config['num_two']
        )

    @solid
    def apply_to_three(context):
        return context.resources.op(3)

    return PipelineDefinition(
        name='multi_mode_with_resources',
        solid_defs=[apply_to_three],
        mode_defs=[
            ModeDefinition(name='add_mode', resource_defs={'op': adder_resource}),
            ModeDefinition(name='mult_mode', resource_defs={'op': multer_resource}),
            ModeDefinition(
                name='double_adder_mode',
                resource_defs={'op': double_adder_resource},
                description='Mode that adds two numbers to thing',
            ),
        ],
        preset_defs=[
            PresetDefinition.from_files(
                'add',
                mode='add_mode',
                environment_files=[
                    script_relative_path('./environments/multi_mode_with_resources/add_mode.yaml')
                ],
            ),
            PresetDefinition(
                'multiproc',
                mode='add_mode',
                environment_dict={
                    'resources': {'op': {'config': 2}},
                    'execution': {'multiprocess': {}},
                    'storage': {'filesystem': {}},
                },
            ),
        ],
    )


def define_repository():
    return RepositoryDefinition(
        name='dagster_test_repository',
        pipeline_defs=[
            define_empty_pipeline(),
            define_single_mode_pipeline(),
            define_multi_mode_pipeline(),
            define_multi_mode_with_resources_pipeline(),
        ],
    )


def test_repository_construction():
    assert define_repository()


def test_empty_repo():
    return RepositoryDefinition(name='empty_repository', pipeline_defs=[])
