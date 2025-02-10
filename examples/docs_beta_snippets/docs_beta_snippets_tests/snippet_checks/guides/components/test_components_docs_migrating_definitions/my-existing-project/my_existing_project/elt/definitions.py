from dagster import asset
from dagster._core.definitions.definitions_class import Definitions


@asset
def my_elt_asset(): ...


defs = Definitions(assets=[my_elt_asset])
