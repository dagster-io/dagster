from dagster import ModeDefinition, fs_object_manager, pipeline, solid


@solid
def solid1(_):
    return 1


@solid
def solid2(_, a):
    return a + 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": fs_object_manager})])
def my_pipeline():
    solid2(solid1())
