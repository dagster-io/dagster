from dagster import Definitions, asset


@asset
def the_dag__some_task():
    return "asset_value"


@asset
def unrelated():
    return "unrelated_value"


@asset
def the_dag__other_task():
    return "other_task_value"


defs = Definitions(assets=[the_dag__other_task, the_dag__some_task, unrelated])
