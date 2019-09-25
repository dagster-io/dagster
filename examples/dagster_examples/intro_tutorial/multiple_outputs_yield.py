from dagster import Int, Output, OutputDefinition, pipeline, solid


@solid(
    output_defs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def yield_outputs(_context):
    yield Output(23, 'out_one')
    yield Output(45, 'out_two')


@solid
def log_num(context, num: int):
    context.log.info('num {num}'.format(num=num))
    return num


@solid
def log_num_squared(context, num: int):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


@pipeline
def multiple_outputs_yield_pipeline():
    out_one, out_two = yield_outputs()
    log_num(out_one)
    log_num_squared(out_two)
