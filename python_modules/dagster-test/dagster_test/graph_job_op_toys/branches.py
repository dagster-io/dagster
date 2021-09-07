from time import sleep

from dagster import Field, Int, Out, Output, graph, op


@op(
    config_schema={"sleep_secs": Field([int], is_required=False, default_value=[0, 0])},
    out={"out_1": Out(Int), "out_2": Out(Int)},
)
def root(context):
    sleep_secs = context.op_config["sleep_secs"]
    yield Output(sleep_secs[0], "out_1")
    yield Output(sleep_secs[1], "out_2")


@op
def branch_op(context, sec):
    if sec < 0:
        sleep(-sec)
        raise Exception("fail")
    context.log.info("Sleeping for {} seconds".format(sec))
    sleep(sec)
    return sec


def make_branch(name, arg, op_num):
    out = arg
    for i in range(op_num):
        out = branch_op.alias(f"{name}_{i}")(out)

    return out


@graph(description="Demo fork-shaped graph that has two-path parallel structure of ops.")
def branch():
    out_1, out_2 = root()
    make_branch("branch_1", out_1, 3)
    make_branch("branch_2", out_2, 5)


branch_failed_job = branch.to_job(
    name="branch_failed",
    config={
        "ops": {"root": {"config": {"sleep_secs": [-10, 30]}}},
    },
)

branch_job = branch.to_job(
    config={
        "ops": {"root": {"config": {"sleep_secs": [0, 10]}}},
    },
)
