# pylint:disable=no-member

from time import sleep

from dagster import Field, In, Int, List, Out, Output, op
from dagster._core.test_utils import default_mode_def_for_test
from dagster._legacy import PresetDefinition, pipeline


@op(
    ins={"units": In(List[Int])},
    out={
        "total": Out(
            Int,
        )
    },
)
def sleeper(context, units):
    tot = 0
    for sec in units:
        context.log.info("Sleeping for {} seconds".format(sec))
        sleep(sec)
        tot += sec

    return tot


@op(
    config_schema=Field([int], is_required=False, default_value=[1, 1, 1, 1]),
    out={
        "out_1": Out(
            List[Int],
        ),
        "out_2": Out(
            List[Int],
        ),
        "out_3": Out(
            List[Int],
        ),
        "out_4": Out(
            List[Int],
        ),
    },
)
def giver(context):
    units = context.op_config
    queues = [[], [], [], []]
    for i, sec in enumerate(units):
        queues[i % 4].append(sec)

    yield Output(queues[0], "out_1")
    yield Output(queues[1], "out_2")
    yield Output(queues[2], "out_3")
    yield Output(queues[3], "out_4")


@op(
    ins={"in_1": In(Int), "in_2": In(Int), "in_3": In(Int), "in_4": In(Int)},
    out=Out(Int),
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
                "execution": {"multiprocess": {}},
                "solids": {"giver": {"config": [2, 2, 2, 2]}},
            },
        )
    ],
    mode_defs=[default_mode_def_for_test],
)
def sleepy_pipeline():
    giver_res = giver()

    total(
        in_1=sleeper(units=giver_res.out_1),
        in_2=sleeper(units=giver_res.out_2),
        in_3=sleeper(units=giver_res.out_3),
        in_4=sleeper(units=giver_res.out_4),
    )
