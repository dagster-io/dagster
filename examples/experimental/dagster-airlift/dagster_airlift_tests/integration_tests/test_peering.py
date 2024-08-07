import time
from typing import cast

import pytest
import requests
from dagster import (
    AssetDep,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    MarkdownMetadataValue,
    SensorResult,
    build_sensor_context,
    multi_asset,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.test_utils import instance_for_test
from dagster_airlift import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
    TaskMigrationState,
)


@pytest.mark.flaky(reruns=2)
def test_dag_peering(
    airflow_instance: None,
) -> None:
    """Test that dags can be correctly peered from airflow, and certain metadata properties are retained."""
    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080", username="admin", password="admin"
        ),
        name="airflow_instance",
    )

    @multi_asset(
        specs=[AssetSpec(key=AssetKey(["some", "key"]))],
        op_tags={"airlift/task_id": "print_task", "airlift/dag_id": "print_dag"},
    )
    def first_asset():
        pass

    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["other", "key"]), deps=[AssetSpec(key=AssetKey(["some", "key"]))]
            )
        ]
    )
    def print_dag__downstream_print_task():
        pass

    defs = build_defs_from_airflow_instance(
        airflow_instance=instance,
        orchestrated_defs=Definitions(
            assets=[
                first_asset,
                print_dag__downstream_print_task,
            ],
        ),
        migration_state_override=AirflowMigrationState(
            dags={
                "print_dag": DagMigrationState(
                    tasks={
                        "print_task": TaskMigrationState(migrated=False),
                        "downstream_print_task": TaskMigrationState(migrated=False),
                    }
                )
            },
        ),
    )
    assert defs.assets
    assert len(list(defs.assets)) == 1
    repo_def = defs.get_repository_def()

    assets_defs = list(repo_def.assets_defs_by_key.values())
    assert len(assets_defs) == 3
    dag_def: AssetsDefinition = [  # noqa
        assets_def
        for assets_def in assets_defs
        if assets_def.key == AssetKey(["airflow_instance", "dag", "print_dag"])
    ][0]
    assert dag_def.key == AssetKey(["airflow_instance", "dag", "print_dag"])
    spec_metadata = next(iter(dag_def.specs)).metadata
    assert spec_metadata["Dag ID"] == "print_dag"
    assert spec_metadata["Link to DAG"] == MarkdownMetadataValue(
        "[View DAG](http://localhost:8080/dags/print_dag)"
    )
    assert "Source Code" in spec_metadata

    task_def: AssetsDefinition = [  # noqa
        assets_def for assets_def in assets_defs if assets_def.key == AssetKey(["some", "key"])
    ][0]
    assert len(list(task_def.specs)) == 1
    task_spec = list(task_def.specs)[0]  # noqa
    assert task_spec.metadata["Dag ID"] == "print_dag"
    assert task_spec.metadata["Computed in Task ID"] == "print_task"

    other_task_def: AssetsDefinition = [  # noqa
        assets_def for assets_def in assets_defs if assets_def.key == AssetKey(["other", "key"])
    ][0]
    assert len(list(other_task_def.specs)) == 1
    other_task_spec = list(other_task_def.specs)[0]  # noqa
    assert other_task_spec.metadata["Dag ID"] == "print_dag"
    assert other_task_spec.metadata["Computed in Task ID"] == "downstream_print_task"
    assert other_task_spec.deps == [AssetDep(AssetKey(["some", "key"]))]

    assert defs.sensors
    sensor_def = next(iter(defs.sensors))

    # Kick off a run of the dag
    response = requests.post(
        "http://localhost:8080/api/v1/dags/print_dag/dagRuns", auth=("admin", "admin"), json={}
    )
    assert response.status_code == 200, response.json()
    # Wait until the run enters a terminal state
    terminal_status = None
    while True:
        response = requests.get(
            "http://localhost:8080/api/v1/dags/print_dag/dagRuns", auth=("admin", "admin")
        )
        assert response.status_code == 200, response.json()
        dag_runs = response.json()["dag_runs"]
        if dag_runs[0]["state"] in ["success", "failed"]:
            terminal_status = dag_runs[0]["state"]
            break
        time.sleep(1)
    assert terminal_status == "success"

    # invoke the sensor and check the sensor result. It should contain a new asset materialization for the dag.
    with instance_for_test() as instance:
        sensor_context = build_sensor_context(instance=instance, repository_def=repo_def)
        sensor_result = sensor_def(sensor_context)
        assert isinstance(sensor_result, SensorResult)
        assert len(sensor_result.asset_events) == 3
        dag_mat = [  # noqa
            asset_mat
            for asset_mat in sensor_result.asset_events
            if asset_mat.asset_key == AssetKey(["airflow_instance", "dag", "print_dag"])
        ][0]
        assert dag_mat
        assert "Airflow Run ID" in dag_mat.metadata
        assert "manual" in cast(str, dag_mat.metadata["Airflow Run ID"].value)
        run_id = dag_mat.metadata["Airflow Run ID"].value
        assert dag_mat.metadata["Link to Run"] == MarkdownMetadataValue(
            f"[View Run](http://localhost:8080/dags/print_dag/grid?dag_run_id={run_id}&tab=details)"
        )
        assert dag_mat.metadata["Airflow Config"] == JsonMetadataValue({})

        task_mat = [  # noqa
            asset_mat
            for asset_mat in sensor_result.asset_events
            if asset_mat.asset_key == AssetKey(["some", "key"])
        ][0]

        assert task_mat
        assert "Airflow Run ID" in task_mat.metadata
        assert "manual" in cast(str, task_mat.metadata["Airflow Run ID"].value)
        run_id = task_mat.metadata["Airflow Run ID"].value
        assert task_mat.metadata["Link to Run"] == MarkdownMetadataValue(
            f"[View Run](http://localhost:8080/dags/print_dag/grid?dag_run_id={run_id}&tab=details)"
        )

        other_mat = [  # noqa
            asset_mat
            for asset_mat in sensor_result.asset_events
            if asset_mat.asset_key == AssetKey(["other", "key"])
        ][0]

        assert other_mat
        # other mat should be downstream of task mat
        assert (  # type: ignore
            other_mat.metadata["Creation Timestamp"].value
            >= task_mat.metadata["Creation Timestamp"].value
        )
