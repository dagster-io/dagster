from time import sleep

from dagster import Field, Int, Output, OutputDefinition, PresetDefinition, pipeline, solid
from dagster.core.definitions.decorators.graph import graph


@solid(
    config_schema={"sleep_secs": Field([int], is_required=False, default_value=[0, 0])},
    output_defs=[OutputDefinition(Int, "out_1"), OutputDefinition(Int, "out_2")],
)
def root(context):
    sleep_secs = context.solid_config["sleep_secs"]
    yield Output(sleep_secs[0], "out_1")
    yield Output(sleep_secs[1], "out_2")


@solid
def branch_solid(context, sec):
    if sec < 0:
        sleep(-sec)
        raise Exception("fail")
    context.log.info("Sleeping for {} seconds".format(sec))
    sleep(sec)
    return sec


def branch(name, arg, solid_num):
    out = arg
    for i in range(solid_num):
        out = branch_solid.alias(f"{name}_{i}")(out)

    return out


@graph(description="Demo fork-shaped pipeline that has two-path parallel structure of solids.")
def branch_graph():
    out_1, out_2 = root()
    branch("branch_1", out_1, 3)
    branch("branch_2", out_2, 5)


branch_failed_job = branch_graph.to_job(
    name="branch_failed",
    config={
        "solids": {"root": {"config": {"sleep_secs": [-10, 30]}}},
    },
)

branch_job = branch_graph.to_job(
    config={
        "solids": {"root": {"config": {"sleep_secs": [0, 10]}}},
    },
)
