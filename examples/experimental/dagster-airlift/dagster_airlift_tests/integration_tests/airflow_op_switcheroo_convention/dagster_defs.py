from dagster import Definitions, asset


@asset
def the_dag__some_task():
    return "asset_value"


defs = Definitions(assets=[the_dag__some_task])
