import random
import time

from dagster import Field, Output, fs_io_manager
from dagster._core.definitions.executor_definition import default_executors
from dagster._legacy import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    pipeline,
    solid,
)


def get_executor_defs():
    try:
        from dagster_dask import dask_executor

        return default_executors + [dask_executor]
    except ImportError:
        return default_executors


@solid(
    input_defs=[InputDefinition("chase_duration", int)],
    output_defs=[OutputDefinition(int, "total")],
    config_schema={
        "chase_size": Field(
            int,
            default_value=100000,
            is_required=False,
            description="How big should the pointer chase array be?",
        )
    },
)
def hammer(context, chase_duration):
    """what better way to do a lot of gnarly work than to pointer chase?"""
    ptr_length = context.solid_config["chase_size"]

    data = list(range(0, ptr_length))
    random.shuffle(data)

    curr = random.randint(0, ptr_length - 1)
    # and away we go
    start_time = time.time()
    while (time.time() - start_time) < chase_duration:
        curr = data[curr]

    context.log.info("Hammered - start %d end %d" % (start_time, time.time()))
    return chase_duration


@solid(
    config_schema=Field(int, is_required=False, default_value=1),
    output_defs=[
        OutputDefinition(int, "out_1"),
        OutputDefinition(int, "out_2"),
        OutputDefinition(int, "out_3"),
        OutputDefinition(int, "out_4"),
    ],
)
def chase_giver(context):
    chase_duration = context.solid_config

    yield Output(chase_duration, "out_1")
    yield Output(chase_duration, "out_2")
    yield Output(chase_duration, "out_3")
    yield Output(chase_duration, "out_4")


@solid(
    input_defs=[
        InputDefinition("in_1", int),
        InputDefinition("in_2", int),
        InputDefinition("in_3", int),
        InputDefinition("in_4", int),
    ],
    output_defs=[OutputDefinition(int)],
)
def reducer(_, in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


@pipeline(
    # Needed for Dask tests which use this pipeline
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
            executor_defs=get_executor_defs(),
        )
    ]
)
def hammer_pipeline():
    out_1, out_2, out_3, out_4 = chase_giver()
    reducer(
        in_1=hammer(chase_duration=out_1),
        in_2=hammer(chase_duration=out_2),
        in_3=hammer(chase_duration=out_3),
        in_4=hammer(chase_duration=out_4),
    )
