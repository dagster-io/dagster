from dagster import Definitions, asset
from dagster_airlift.core.utils import metadata_for_task_mapping


@asset(metadata=metadata_for_task_mapping(dag_id="the_dag", task_id="some_task"))
def the_dag__some_task():
    return "asset_value"


@asset
def unrelated():
    return "unrelated_value"


@asset(metadata=metadata_for_task_mapping(dag_id="the_dag", task_id="other_task"))
def the_dag__other_task():
    return "other_task_value"


defs = Definitions(assets=[the_dag__other_task, the_dag__some_task, unrelated])
