import typing
from time import sleep

from dagster import Config, In, Int, List, Out, Output, job, op
from pydantic import Field


@op(
    ins={"units": In(List[Int])},
    out={"total": Out(Int)},
)
def sleeper(context, units):
    tot = 0
    for sec in units:
        context.log.info(f"Sleeping for {sec} seconds")
        sleep(sec)
        tot += sec

    return tot


class GiverConfig(Config):
    units: list[int] = Field(default_value=[1, 1, 1, 1])  # type: ignore


@op(
    out={
        "out 1": Out(List[Int]),
        "out 2": Out(List[Int]),
        "out 3": Out(List[Int]),
        "out 4": Out(List[Int]),
    },
)
def giver(config: GiverConfig):
    queues = [[], [], [], []]
    for i, sec in enumerate(config.units):
        queues[i % 4].append(sec)

    yield Output(queues[0], "out_1")
    yield Output(queues[1], "out_2")
    yield Output(queues[2], "out_3")
    yield Output(queues[3], "out_4")


@op(
    ins={
        "in_1": In(Int),
        "in_2": In(Int),
        "in_3": In(Int),
        "in_4": In(Int),
    },
    out=Out(int),
)
def total(_, in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


@job(
    description="Demo diamond-shaped job that has four-path parallel structure of ops.",
)
def sleepy_job():
    giver_res = giver()

    total(
        in_1=sleeper(units=giver_res.out_1),
        in_2=sleeper(units=giver_res.out_2),
        in_3=sleeper(units=giver_res.out_3),
        in_4=sleeper(units=giver_res.out_4),
    )
