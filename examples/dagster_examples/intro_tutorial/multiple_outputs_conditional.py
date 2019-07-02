# pylint: disable=no-value-for-parameter
from dagster import Field, Int, OutputDefinition, Output, String, pipeline, solid


@solid(
    config_field=Field(String, description='Should be either out_one or out_two'),
    output_defs=[
        OutputDefinition(dagster_type=Int, name='out_one', is_optional=True),
        OutputDefinition(dagster_type=Int, name='out_two', is_optional=True),
    ],
)
def conditional(context):
    if context.solid_config == 'out_one':
        yield Output(23, 'out_one')
    elif context.solid_config == 'out_two':
        yield Output(45, 'out_two')
    else:
        raise Exception('invalid config')


@solid
def log_num(context, num: int):
    context.log.info('num {num}'.format(num=num))
    return num


@solid
def log_num_squared(context, num: int):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


@pipeline
def multiple_outputs_conditional_pipeline():
    out_one, out_two = conditional()
    log_num(out_one)
    log_num_squared(out_two)
