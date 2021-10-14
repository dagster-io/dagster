# start_marker
from dagster import ModeDefinition, OutputDefinition, fs_io_manager, mem_io_manager, pipeline, solid


@solid(output_defs=[OutputDefinition(io_manager_key="fs")])
def solid1():
    return 1


@solid(output_defs=[OutputDefinition(io_manager_key="mem")])
def solid2(a):
    return a + 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"fs": fs_io_manager, "mem": mem_io_manager})])
def my_pipeline():
    solid2(solid1())


# end_marker
