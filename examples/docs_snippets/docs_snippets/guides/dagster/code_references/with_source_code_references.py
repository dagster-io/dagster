from dagster import Definitions, asset, with_source_code_references


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(assets=with_source_code_references([my_asset, another_asset]))
