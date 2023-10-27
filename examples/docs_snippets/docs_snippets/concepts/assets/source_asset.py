def execute_query(query):
    pass


# start_marker
from dagster import AssetKey, SourceAsset, asset

my_source_asset = SourceAsset(key=AssetKey("a_source_asset"))


@asset(deps=[my_source_asset])
def my_derived_asset():
    return execute_query("SELECT * from a_source_asset").as_list() + [4]


# end_marker


# start_argument_dependency


@asset
def my_other_derived_asset(a_source_asset):
    return a_source_asset + [4]


# end_argument_dependency
