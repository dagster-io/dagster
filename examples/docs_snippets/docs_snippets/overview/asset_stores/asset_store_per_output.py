"""isort:skip_file"""
from docs_snippets.overview.asset_stores.custom_asset_store import my_asset_store

# start_marker
from dagster import ModeDefinition, OutputDefinition, fs_asset_store, pipeline, solid


@solid(output_defs=[OutputDefinition(asset_store_key="db_asset_store")])
def solid1(_):
    """Return a Pandas DataFrame"""


@solid
def solid2(_, _input_dataframe):
    """Return some object"""


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "asset_store": fs_asset_store,
                "db_asset_store": my_asset_store,  # defined in code snippet above
            }
        )
    ]
)
def my_pipeline():
    solid2(solid1())


# end_marker
