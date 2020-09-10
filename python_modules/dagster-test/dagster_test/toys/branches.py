from time import sleep

from dagster import Field, Int, Output, OutputDefinition, PresetDefinition, pipeline, solid


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


@pipeline(
    description=("Demo fork-shaped pipeline that has two-path parallel structure of solids."),
    preset_defs=[
        PresetDefinition(
            "sleep_failed",
            {
                "storage": {"filesystem": {}},
                "execution": {"multiprocess": {}},
                "solids": {"root": {"config": {"sleep_secs": [-10, 30]}}},
            },
        ),
        PresetDefinition(
            "sleep",
            {
                "storage": {"filesystem": {}},
                "execution": {"multiprocess": {}},
                "solids": {"root": {"config": {"sleep_secs": [0, 10]}}},
            },
        ),
    ],
)
def branch_pipeline():
    out_1, out_2 = root()
    branch("branch_1", out_1, 3)
    branch("branch_2", out_2, 5)
