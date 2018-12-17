from dagster import (
    Field,
    PipelineDefinition,
    execute_pipeline,
    solid,
    types,
)


@solid(config_field=Field(types.String))
def hello_world(info):
    return info.config


def define_configurable_hello_world_pipeline():
    return PipelineDefinition(name='part_four_pipeline', solids=[hello_world])


if __name__ == '__main__':
    execute_pipeline(
        define_configurable_hello_world_pipeline(),
        {
            'solids': {
                'hello_world': {
                    'config': 'Hello, World!',
                },
            },
        },
    )
