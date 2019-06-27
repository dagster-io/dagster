import random
import time

from dagster import (
    DependencyDefinition,
    Dict,
    ExecutionTargetHandle,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    PipelineDefinition,
    Output,
    SolidInvocation,
    lambda_solid,
    solid,
)
from dagster_dask import execute_on_dask
from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.system_storage import s3_plus_default_storage_defs


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
    config_field=Field(Int, is_optional=True, default_value=1),
    outputs=[
        OutputDefinition(Int, 'out_1'),
        OutputDefinition(Int, 'out_2'),
        OutputDefinition(Int, 'out_3'),
        OutputDefinition(Int, 'out_4'),
    ],
)
def giver(context):
    chase_duration = context.solid_config

    yield Output(chase_duration, 'out_1')
    yield Output(chase_duration, 'out_2')
    yield Output(chase_duration, 'out_3')
    yield Output(chase_duration, 'out_4')


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
        solid_defs=[giver, hammer, total],
        dependencies={
            SolidInvocation('giver'): {},
            SolidInvocation('hammer', alias='hammer_1'): {
                'chase_duration': DependencyDefinition('giver', 'out_1')
            },
            SolidInvocation('hammer', alias='hammer_2'): {
                'chase_duration': DependencyDefinition('giver', 'out_2')
            },
            SolidInvocation('hammer', alias='hammer_3'): {
                'chase_duration': DependencyDefinition('giver', 'out_3')
            },
            SolidInvocation('hammer', alias='hammer_4'): {
                'chase_duration': DependencyDefinition('giver', 'out_4')
            },
            SolidInvocation('total'): {
                'in_1': DependencyDefinition('hammer_1', 'total'),
                'in_2': DependencyDefinition('hammer_2', 'total'),
                'in_3': DependencyDefinition('hammer_3', 'total'),
                'in_4': DependencyDefinition('hammer_4', 'total'),
            },
        },
        mode_definitions=[
            ModeDefinition(
                resources={'s3': s3_resource}, system_storage_defs=s3_plus_default_storage_defs
            )
        ],
    )


if __name__ == '__main__':
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_fn(define_hammer_pipeline),
        env_config={'storage': {'filesystem': {}}},
    )
    print('Total Hammer Time: ', result.result_for_solid('total').result_value())
