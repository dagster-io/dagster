from dagster import Definitions, asset
from dagster_airlift.core import dag_defs, task_defs


@asset
def my_asset_for_some_task():
    return "asset_value"


defs = dag_defs(
    "the_dag",
    task_defs("some_task", Definitions(assets=[my_asset_for_some_task])),
)
