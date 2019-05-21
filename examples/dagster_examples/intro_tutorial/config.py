# encoding: utf-8
# py27 compat

from dagster import Field, PipelineDefinition, execute_pipeline, solid, types


@solid(config_field=Field(types.String, is_optional=True, default_value='en-us'))
def configurable_hello(context):
    if len(context.solid_config) >= 3 and context.solid_config[:3] == 'haw':
        return 'Aloha honua!'
    elif len(context.solid_config) >= 2 and context.solid_config[:2] == 'cn':
        return '你好, 世界!'
    else:
        return 'Hello, world!'


def define_configurable_hello_pipeline():
    return PipelineDefinition(name='configurable_hello_pipeline', solids=[configurable_hello])


def test_intro_tutorial_part_four():
    execute_pipeline(
        define_configurable_hello_pipeline(), {'solids': {'configurable_hello': {'config': 'cn'}}}
    )
