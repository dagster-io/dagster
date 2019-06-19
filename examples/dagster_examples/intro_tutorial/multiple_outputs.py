# pylint: disable=no-value-for-parameter
from dagster import Int, MultipleResults, OutputDefinition, pipeline, solid


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def return_dict_results(_context):
    return MultipleResults.from_dict({'out_one': 23, 'out_two': 45})


@solid
def log_num(context, num: int):
    context.log.info('num {num}'.format(num=num))
    return num


@solid
def log_num_squared(context, num: int):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


@pipeline
def multiple_outputs_pipeline(_):
    out_one, out_two = return_dict_results()
    log_num(out_one)
    log_num_squared(out_two)
