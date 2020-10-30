from dagster import ModeDefinition, fs_asset_store, pipeline, solid


@solid
def solid1(_):
    return 1


@solid
def solid2(_, a):
    return a + 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_store": fs_asset_store})])
def my_pipeline():
    solid2(solid1())
