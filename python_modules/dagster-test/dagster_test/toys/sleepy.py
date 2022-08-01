# pylint:disable=no-member
from time import sleep
from typing import Iterator, List

from dagster import Field, Output, graph
from dagster._legacy import OutputDefinition, solid


@solid
def sleeper(context, units: List[int]) -> int:
    tot = 0
    for sec in units:
        context.log.info("Sleeping for {} seconds".format(sec))
        sleep(sec)
        tot += sec

    return tot


@solid(
    config_schema=[int],
    output_defs=[
        OutputDefinition(List[int], "out_1"),
        OutputDefinition(List[int], "out_2"),
        OutputDefinition(List[int], "out_3"),
        OutputDefinition(List[int], "out_4"),
    ],
)
def giver(context) -> Iterator[Output]:
    units = context.solid_config
    queues: List[List[int]] = [[], [], [], []]
    for i, sec in enumerate(units):
        queues[i % 4].append(sec)

    yield Output(queues[0], "out_1")
    yield Output(queues[1], "out_2")
    yield Output(queues[2], "out_3")
    yield Output(queues[3], "out_4")


@solid(
    config_schema={"fail": Field(bool, is_required=False, default_value=False)},
    output_defs=[OutputDefinition(int, is_required=False)],
)
def total(context, in_1, in_2, in_3, in_4):
    result = in_1 + in_2 + in_3 + in_4
    if context.solid_config["fail"]:
        yield Output(result, "result")
    # skip the failing solid
    context.log.info(str(result))


@solid
def will_fail(_, i):
    raise Exception(i)


@graph(
    description=(
        "Demo diamond-shaped pipeline that has four-path parallel structure of solids.  Execute "
        "with the `multi` preset to take advantage of multi-process parallelism."
    ),
)
def sleepy():
    giver_res = giver()

    will_fail(
        total(
            in_1=sleeper(units=giver_res.out_1),
            in_2=sleeper(units=giver_res.out_2),
            in_3=sleeper(units=giver_res.out_3),
            in_4=sleeper(units=giver_res.out_4),
        )
    )


def _config(cfg):
    return {
        "solids": {
            "giver": {"config": cfg["sleeps"]},
            "total": {"config": {"fail": cfg["fail"]}},
        },
    }


sleepy_pipeline = sleepy.to_job(
    config={
        "solids": {"giver": {"config": [2, 2, 2, 2]}},
    },
)
