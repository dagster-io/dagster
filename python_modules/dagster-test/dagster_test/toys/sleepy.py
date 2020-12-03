# pylint:disable=no-member

from time import sleep

from dagster import (
    Field,
    InputDefinition,
    Int,
    List,
    Output,
    OutputDefinition,
    PresetDefinition,
    pipeline,
    solid,
)


@solid(
    input_defs=[InputDefinition("units", List[Int])], output_defs=[OutputDefinition(Int, "total")]
)
def sleeper(context, units):
    tot = 0
    for sec in units:
        context.log.info("Sleeping for {} seconds".format(sec))
        sleep(sec)
        tot += sec

    return tot


@solid(
    config_schema=Field([int], is_required=False, default_value=[1, 1, 1, 1]),
    output_defs=[
        OutputDefinition(List[Int], "out_1"),
        OutputDefinition(List[Int], "out_2"),
        OutputDefinition(List[Int], "out_3"),
        OutputDefinition(List[Int], "out_4"),
    ],
)
def giver(context):
    units = context.solid_config
    queues = [[], [], [], []]
    for i, sec in enumerate(units):
        queues[i % 4].append(sec)

    yield Output(queues[0], "out_1")
    yield Output(queues[1], "out_2")
    yield Output(queues[2], "out_3")
    yield Output(queues[3], "out_4")


@solid(
    input_defs=[
        InputDefinition("in_1", Int),
        InputDefinition("in_2", Int),
        InputDefinition("in_3", Int),
        InputDefinition("in_4", Int),
    ],
    output_defs=[OutputDefinition(Int)],
)
def total(_, in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


@pipeline(
    description=(
        "Demo diamond-shaped pipeline that has four-path parallel structure of solids.  Execute "
        "with the `multi` preset to take advantage of multi-process parallelism."
    ),
    preset_defs=[
        PresetDefinition(
            "multi",
            {
                "intermediate_storage": {"filesystem": {}},
                "execution": {"multiprocess": {}},
                "solids": {"giver": {"config": [2, 2, 2, 2]}},
            },
        )
    ],
)
def sleepy_pipeline():
    giver_res = giver()

    total(
        in_1=sleeper(units=giver_res.out_1),
        in_2=sleeper(units=giver_res.out_2),
        in_3=sleeper(units=giver_res.out_3),
        in_4=sleeper(units=giver_res.out_4),
    )
