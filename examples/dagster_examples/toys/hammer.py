import random
import time

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.system_storage import s3_plus_default_storage_defs

from dagster import (
    Dict,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    Output,
    OutputDefinition,
    pipeline,
    solid,
)
from dagster.core.definitions.executor import default_executors


def get_executor_defs():
    try:
        from dagster_dask import dask_executor

        return default_executors + [dask_executor]
    except ImportError:
        return default_executors


@solid(
    input_defs=[InputDefinition('chase_duration', Int)],
    output_defs=[OutputDefinition(Int, 'total')],
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
    output_defs=[
        OutputDefinition(Int, 'out_1'),
        OutputDefinition(Int, 'out_2'),
        OutputDefinition(Int, 'out_3'),
        OutputDefinition(Int, 'out_4'),
    ],
)
def chase_giver(context):
    chase_duration = context.solid_config

    yield Output(chase_duration, 'out_1')
    yield Output(chase_duration, 'out_2')
    yield Output(chase_duration, 'out_3')
    yield Output(chase_duration, 'out_4')


@solid(
    input_defs=[
        InputDefinition('in_1', Int),
        InputDefinition('in_2', Int),
        InputDefinition('in_3', Int),
        InputDefinition('in_4', Int),
    ],
    output_defs=[OutputDefinition(Int)],
)
def reducer(_, in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


@pipeline(
    # Needed for Dask tests which use this pipeline
    mode_defs=[
        ModeDefinition(
            resource_defs={'s3': s3_resource},
            system_storage_defs=s3_plus_default_storage_defs,
            executor_defs=get_executor_defs(),
        )
    ]
)
def hammer_pipeline():
    # pylint: disable=no-value-for-parameter
    out_1, out_2, out_3, out_4 = chase_giver()
    return reducer(
        in_1=hammer.alias('hammer_1')(chase_duration=out_1),
        in_2=hammer.alias('hammer_2')(chase_duration=out_2),
        in_3=hammer.alias('hammer_3')(chase_duration=out_3),
        in_4=hammer.alias('hammer_4')(chase_duration=out_4),
    )
