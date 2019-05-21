from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    Result,
    solid,
    String,
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


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def return_dict_results(_context):
    return MultipleResults.from_dict({'out_one': 23, 'out_two': 45})


@solid(
    config_field=Field(String, description='Should be either out_one or out_two'),
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one', is_optional=True),
        OutputDefinition(dagster_type=Int, name='out_two', is_optional=True),
    ],
)
def conditional(context):
    if context.solid_config == 'out_one':
        yield Result(23, 'out_one')
    elif context.solid_config == 'out_two':
        yield Result(45, 'out_two')
    else:
        raise Exception('invalid config')


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num(context, num):
    context.log.info('num {num}'.format(num=num))
    return num


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num_squared(context, num):
    context.log.info('num_squared {num_squared}'.format(num_squared=num * num))
    return num * num


def define_multiple_outputs_step_one_pipeline():
    return PipelineDefinition(
        name='multiple_outputs_step_one_pipeline',
        solids=[return_dict_results, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition(solid='return_dict_results', output='out_one')},
            'log_num_squared': {
                'num': DependencyDefinition(solid='return_dict_results', output='out_two')
            },
        },
    )


def define_multiple_outputs_step_two_pipeline():
    return PipelineDefinition(
        name='multiple_outputs_step_two_pipeline',
        solids=[yield_outputs, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition('yield_outputs', 'out_one')},
            'log_num_squared': {'num': DependencyDefinition('yield_outputs', 'out_two')},
        },
    )


def define_multiple_outputs_step_three_pipeline():
    return PipelineDefinition(
        name='multiple_outputs_step_three_pipeline',
        solids=[conditional, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition('conditional', 'out_one')},
            'log_num_squared': {'num': DependencyDefinition('conditional', 'out_two')},
        },
    )
