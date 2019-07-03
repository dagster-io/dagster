'''
Repository of test pipelines
'''

from dagster import (
    Field,
    Int,
    ModeDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    resource,
    solid,
)


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
    @resource(config_field=Field(Int))
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_field=Field(Int))
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config={'num_one': Field(Int), 'num_two': Field(Int)})
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
    )


def define_repository():
    return RepositoryDefinition.eager_construction(
        name='dagster_test_repository',
        pipelines=[
            define_empty_pipeline(),
            define_single_mode_pipeline(),
            define_multi_mode_pipeline(),
            define_multi_mode_with_resources_pipeline(),
        ],
    )


def test_repository_construction():
    assert define_repository()
