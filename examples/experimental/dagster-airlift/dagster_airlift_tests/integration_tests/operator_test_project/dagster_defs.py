from dagster import Definitions, asset
from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY


@asset(metadata={DAG_ID_METADATA_KEY: "the_dag", TASK_ID_METADATA_KEY: "some_task"})
def the_dag__some_task():
    return "asset_value"


@asset
def unrelated():
    return "unrelated_value"


@asset(metadata={DAG_ID_METADATA_KEY: "the_dag", TASK_ID_METADATA_KEY: "other_task"})
def the_dag__other_task():
    return "other_task_value"


defs = Definitions(assets=[the_dag__other_task, the_dag__some_task, unrelated])
