from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    solid,
    Int,
)


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def yield_outputs(_context):
    yield Result(23, 'out_one')
    yield Result(45, 'out_two')


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num(context, num):
    context.log.info('num {num}'.format(num=num))
    return num


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num_squared(context, num):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


def define_multiple_outputs_yield_pipeline():
    return PipelineDefinition(
        name='multiple_outputs_yield_pipeline',
        solid_defs=[yield_outputs, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition('yield_outputs', 'out_one')},
            'log_num_squared': {'num': DependencyDefinition('yield_outputs', 'out_two')},
        },
    )
