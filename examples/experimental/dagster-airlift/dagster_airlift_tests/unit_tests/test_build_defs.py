from dagster import (
    AssetKey,
    AssetSpec,
    Definitions,
    asset,
    asset_check,
    executor,
    job,
    logger,
    schedule,
    sensor,
)
from dagster_airlift.core import build_defs_from_airflow_instance
from dagster_airlift.core.airflow_instance import DagInfo

from .conftest import make_test_instance


@executor
def nonstandard_executor(init_context):
    pass


@logger
def nonstandard_logger(init_context):
    pass


@sensor(job_name="the_job")
def some_sensor():
    pass


@schedule(cron_schedule="0 0 * * *", job_name="the_job")
def some_schedule():
    pass


@asset
def dag__task():
    pass


@asset
def a():
    pass


@asset_check(asset=a)
def a_check():
    pass


@asset_check(asset=dag__task)
def other_check():
    pass


@job
def the_job():
    pass


def test_defs_passthrough() -> None:
    """Test that passed-through definitions are present in the final definitions."""
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_test_instance(),
        defs=Definitions(
            assets=[a],
            asset_checks=[a_check],
            jobs=[the_job],
            sensors=[some_sensor],
            schedules=[some_schedule],
            loggers={"the_logger": nonstandard_logger},
            executor=nonstandard_executor,
        ),
    )
    assert defs.executor == nonstandard_executor
    assert defs.loggers
    assert len(defs.loggers) == 1
    assert next(iter(defs.loggers.keys())) == "the_logger"
    assert defs.sensors
    assert len(list(defs.sensors)) == 2
    our_sensor = next(
        iter(sensor_def for sensor_def in defs.sensors if sensor_def.name == "some_sensor")
    )
    assert our_sensor == some_sensor
    assert defs.schedules
    assert len(list(defs.schedules)) == 1
    assert next(iter(defs.schedules)) == some_schedule
    assert defs.jobs
    assert len(list(defs.jobs)) == 1
    assert next(iter(defs.jobs)) == the_job


def test_coerce_specs() -> None:
    def list_dags(self):
        return [
            DagInfo(
                webserver_url="http://localhost:8080", dag_id="dag", metadata={"file_token": "blah"}
            ),
        ]

    spec = AssetSpec(key="a", tags={"airlift/dag_id": "dag", "airlift/task_id": "task"})
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_test_instance(list_dags_override=list_dags),
        defs=Definitions(
            assets=[spec],
        ),
    )
    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) == 2
    assert AssetKey("a") in repo.assets_defs_by_key
    assets_def = repo.assets_defs_by_key[AssetKey("a")]
    # Asset metadata properties have been glommed onto the asset
    assert next(iter(assets_def.specs)).metadata["Dag ID"] == "dag"


def test_invalid_dagster_named_tasks_and_dags() -> None:
    """Test that invalid dagster names are converted to valid names."""

    def list_dags(self):
        return [
            DagInfo(
                webserver_url="http://localhost:8080",
                dag_id="dag-with-hyphens",
                metadata={"file_token": "blah"},
            ),
        ]

    spec = AssetSpec(
        key="a", tags={"airlift/dag_id": "dag-with-hyphens", "airlift/task_id": "task-with-hyphens"}
    )
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_test_instance(list_dags_override=list_dags),
        defs=Definitions(
            assets=[spec],
        ),
    )

    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) == 2
    assert AssetKey("a") in repo.assets_defs_by_key
    assets_def = repo.assets_defs_by_key[AssetKey("a")]
    assert assets_def.node_def.name == "dag_with_hyphens__task_with_hyphens"

    assert AssetKey(["airflow_instance", "dag", "dag_with_hyphens"]) in repo.assets_defs_by_key
    dag_def = repo.assets_defs_by_key[AssetKey(["airflow_instance", "dag", "dag_with_hyphens"])]
    assert dag_def.node_def.name == "airflow_instance__dag__dag_with_hyphens"
