from dagster import Definitions, JsonMetadataValue, asset
from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY


@asset(metadata={AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("the_dag", "some_task")])})
def the_dag__some_task():
    return "asset_value"


@asset
def unrelated():
    return "unrelated_value"


@asset(metadata={AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("the_dag", "other_task")])})
def the_dag__other_task():
    return "other_task_value"


defs = Definitions(assets=[the_dag__other_task, the_dag__some_task, unrelated])
