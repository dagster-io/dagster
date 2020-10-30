"""isort:skip_file"""
from dagster import solid


@solid
def solid1(_):
    pass


@solid
def solid2(_, _a):
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
from dagster import AssetStore, ModeDefinition, pipeline, resource


class MyAssetStore(AssetStore):
    def set_asset(self, context, obj):
        # output_name is the name given to the OutputDefinition that we're storing for
        table_name = context.output_name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def get_asset(self, context):
        # output_name is the name given to the OutputDefinition that we're retrieving for
        table_name = context.output_name
        return read_dataframe_from_table(name=table_name)


@resource
def my_asset_store(_):
    return MyAssetStore()


@pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_store": my_asset_store})])
def my_pipeline():
    solid2(solid1())


# end_marker
