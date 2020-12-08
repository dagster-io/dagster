# start_marker
from dagster import (
    ModeDefinition,
    OutputDefinition,
    fs_object_manager,
    mem_object_manager,
    pipeline,
    solid,
)


@solid(output_defs=[OutputDefinition(manager_key="fs")])
def solid1(_):
    return 1


@solid(output_defs=[OutputDefinition(manager_key="mem")])
def solid2(_, a):
    return a + 1


@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"fs": fs_object_manager, "mem": mem_object_manager})]
)
def my_pipeline():
    solid2(solid1())


# end_marker
