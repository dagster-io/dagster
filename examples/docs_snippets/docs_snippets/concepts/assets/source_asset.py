def execute_query(query):
    pass


# start_marker
from dagster import AssetKey, SourceAsset, asset

cereals_source_asset = SourceAsset(key=AssetKey("cereals"))


@asset(deps=[cereals_source_asset])
def sugary_cereals() -> None:
    execute_query(
        "CREATE TABLE sugary_cereals AS SELECT * FROM cereals WHERE sugar_grams > 10"
    )


# end_marker


# start_argument_dependency


@asset
def fiber_cereals(a_source_asset):
    return a_source_asset + [4]


# end_argument_dependency
