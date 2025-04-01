from time import sleep

from dagster import Field, Out, Output, graph, op
from dagster._core.execution.context.compute import OpExecutionContext


@op
def sleeper(context, units: list[int]) -> int:
    tot = 0
    for sec in units:
        context.log.info(f"Sleeping for {sec} seconds")
        sleep(sec)
        tot += sec

    return tot


@op(
    config_schema=[int],
    out={
        "out_1": Out(list[int]),
        "out_2": Out(list[int]),
        "out_3": Out(list[int]),
        "out_4": Out(list[int]),
    },
)
def giver(context: OpExecutionContext) -> tuple[list[int], list[int], list[int], list[int]]:
    units = context.op_config
    queues: list[list[int]] = [[], [], [], []]
    for i, sec in enumerate(units):
        queues[i % 4].append(sec)

    return queues[0], queues[1], queues[2], queues[3]


@op(
    config_schema={"fail": Field(bool, is_required=False, default_value=False)},
    out=Out(int, is_required=False),
)
def total(context, in_1, in_2, in_3, in_4):
    result = in_1 + in_2 + in_3 + in_4
    if context.op_config["fail"]:
        yield Output(result, "result")
    # skip the failing op
    context.log.info(str(result))


@op
def will_fail(i):
    raise Exception(i)


@graph(
    description="Demo diamond-shaped graph that has four-path parallel structure of ops.",
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


sleepy_job = sleepy.to_job(
    config={
        "ops": {"giver": {"config": [2, 2, 2, 2]}},
    },
)
