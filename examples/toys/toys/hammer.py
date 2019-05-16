import random
import time

from dagster import (
    DependencyDefinition,
    Dict,
    ExecutionTargetHandle,
    Field,
    InputDefinition,
    Int,
    MultiprocessExecutorConfig,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidInstance,
    RunConfig,
    execute_pipeline,
    lambda_solid,
    solid,
    RunStorageMode,
)


@solid(
    inputs=[InputDefinition('chase_duration', Int)],
    outputs=[OutputDefinition(Int, 'total')],
    config_field=Field(
        Dict(
            fields={
                'chase_size': Field(
                    Int,
                    default_value=100000,
                    is_optional=True,
                    description='How big should the pointer chase array be?',
                )
            }
        )
    ),
)
def hammer(context, chase_duration):
    '''what better way to do a lot of gnarly work than to pointer chase?'''
    ptr_length = context.solid_config['chase_size']

    data = list(range(0, ptr_length))
    random.shuffle(data)

    curr = random.randint(0, ptr_length)
    # and away we go
    start_time = time.time()
    while (time.time() - start_time) < chase_duration:
        curr = data[curr]

    context.log.info('Hammered - start %d end %d' % (start_time, time.time()))
    return chase_duration


@solid(
    config_field=Field(Int, is_optional=True, default_value=5),
    outputs=[
        OutputDefinition(Int, 'out_1'),
        OutputDefinition(Int, 'out_2'),
        OutputDefinition(Int, 'out_3'),
        OutputDefinition(Int, 'out_4'),
    ],
)
def giver(context):
    chase_duration = context.solid_config

    yield Result(chase_duration, 'out_1')
    yield Result(chase_duration, 'out_2')
    yield Result(chase_duration, 'out_3')
    yield Result(chase_duration, 'out_4')


@lambda_solid(
    inputs=[
        InputDefinition('in_1', Int),
        InputDefinition('in_2', Int),
        InputDefinition('in_3', Int),
        InputDefinition('in_4', Int),
    ],
    output=OutputDefinition(Int),
)
def total(in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


def define_hammer_pipeline():
    return PipelineDefinition(
        name="thors_hammer",
        solids=[giver, hammer, total],
        dependencies={
            SolidInstance('giver'): {},
            SolidInstance('hammer', alias='hammer_1'): {
                'chase_duration': DependencyDefinition('giver', 'out_1')
            },
            SolidInstance('hammer', alias='hammer_2'): {
                'chase_duration': DependencyDefinition('giver', 'out_2')
            },
            SolidInstance('hammer', alias='hammer_3'): {
                'chase_duration': DependencyDefinition('giver', 'out_3')
            },
            SolidInstance('hammer', alias='hammer_4'): {
                'chase_duration': DependencyDefinition('giver', 'out_4')
            },
            SolidInstance('total'): {
                'in_1': DependencyDefinition('hammer_1', 'total'),
                'in_2': DependencyDefinition('hammer_2', 'total'),
                'in_3': DependencyDefinition('hammer_3', 'total'),
                'in_4': DependencyDefinition('hammer_4', 'total'),
            },
        },
    )


if __name__ == '__main__':
    pipeline = define_hammer_pipeline()
    result = execute_pipeline(
        pipeline,
        run_config=RunConfig(
            executor_config=MultiprocessExecutorConfig(
                exc_target_handle=ExecutionTargetHandle.for_pipeline_fn(define_hammer_pipeline)
            ),
            storage_mode=RunStorageMode.FILESYSTEM,
        ),
    )

    print('Total Hammer Time: ', result.result_for_solid('total').transformed_value())
