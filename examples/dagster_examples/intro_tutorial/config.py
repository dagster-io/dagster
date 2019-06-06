# encoding: utf-8
# py27 compat

from dagster import execute_pipeline, solid, Field, PipelineDefinition, String


@solid(config_field=Field(String, is_optional=True, default_value='en-us'))
def hello_with_config(context):
    if context.solid_config == 'haw':
        return 'Aloha honua!'
    elif context.solid_config == 'cn':
        return '你好, 世界!'
    else:
        return 'Hello, world!'


def define_hello_with_config_pipeline():
    return PipelineDefinition(name='hello_with_config_pipeline', solids=[hello_with_config])


def run():
    execute_pipeline(
        define_hello_with_config_pipeline(), {'solids': {'hello_with_config': {'config': 'cn'}}}
    )


if __name__ == '__main__':
    run()
