from dagster import (
    ConfigDefinition,
    PipelineDefinition,
    execute_pipeline,
    solid,
    types,
)


@solid(config_field=ConfigDefinition(types.String))
def hello_world(info):
    print(info.config)


def define_pipeline():
    return PipelineDefinition(solids=[hello_world])


if __name__ == '__main__':
    execute_pipeline(
        define_pipeline(),
        {
            'solids': {
                'hello_world': {
                    'config': 'Hello, World!',
                },
            },
        },
    )
