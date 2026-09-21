import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset
def another_asset(): ...


defs = dg.Definitions(
    # highlight-start
    # with_source_code_references() automatically attaches the proper metadata
    assets=dg.with_source_code_references([my_asset, another_asset])
    # highlight-end
)
