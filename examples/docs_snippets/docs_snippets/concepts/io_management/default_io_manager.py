from dagster import ModeDefinition, fs_io_manager, pipeline, solid


@solid
def solid1():
    return 1


@solid
def solid2(a):
    return a + 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def my_pipeline():
    solid2(solid1())
