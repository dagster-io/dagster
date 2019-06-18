from dagster import (
    DependencyDefinition,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    solid,
    Int,
)


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def return_dict_results(_context):
    return MultipleResults.from_dict({'out_one': 23, 'out_two': 45})


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num(context, num):
    context.log.info('num {num}'.format(num=num))
    return num


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num_squared(context, num):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


def define_multiple_outputs_pipeline():
    return PipelineDefinition(
        name='multiple_outputs_pipeline',
        solid_defs=[return_dict_results, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition(solid='return_dict_results', output='out_one')},
            'log_num_squared': {
                'num': DependencyDefinition(solid='return_dict_results', output='out_two')
            },
        },
    )
