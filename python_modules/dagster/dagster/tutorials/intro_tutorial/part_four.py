from dagster import Field, PipelineDefinition, execute_pipeline, solid, String


@solid(config_field=Field(String))
def configurable_hello_world(info):
    return info.config


def define_configurable_hello_world_pipeline():
    return PipelineDefinition(
        name='part_four_pipeline', solids=[configurable_hello_world]
    )


def test_intro_tutorial_part_four():
    execute_pipeline(
        define_configurable_hello_world_pipeline(),
        {'solids': {'configurable_hello_world': {'config': 'Hello, World!'}}},
    )
