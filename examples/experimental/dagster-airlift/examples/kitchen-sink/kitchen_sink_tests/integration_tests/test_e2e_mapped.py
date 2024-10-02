import os
import time
from datetime import timedelta
from typing import List

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._time import get_current_datetime
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY

from kitchen_sink_tests.integration_tests.conftest import makefile_dir


def poll_for_materialization(
    dagster_instance: DagsterInstance,
    asset_key: AssetKey,
) -> EventLogEntry:
    start_time = get_current_datetime()
    while get_current_datetime() - start_time < timedelta(seconds=30):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=asset_key
        )

        time.sleep(0.1)
        if asset_materialization:
            return asset_materialization

    raise Exception(f"Timeout waiting for materialization event on {asset_key}")


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> List[str]:
    return ["make", "run_dagster_mapped", "-C", str(makefile_dir())]


def test_migrated_dagster_print_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that materializations register."""
    from kitchen_sink.dagster_defs.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_mats_per_dag = {
        "print_dag": [AssetKey("print_asset")],
    }

    for dag_id, expected_asset_keys in expected_mats_per_dag.items():
        airflow_run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=airflow_run_id, timeout=60)
        dagster_instance = DagsterInstance.get()

        dag_asset_key = AssetKey(["my_airflow_instance", "dag", dag_id])
        assert poll_for_materialization(dagster_instance, dag_asset_key)

        for expected_asset_key in expected_asset_keys:
            mat_event_log_entry = poll_for_materialization(dagster_instance, expected_asset_key)
            assert mat_event_log_entry.asset_materialization
            assert mat_event_log_entry.asset_materialization.asset_key == expected_asset_key

            assert mat_event_log_entry.asset_materialization
            dagster_run_id = mat_event_log_entry.run_id

            all_materializations = dagster_instance.fetch_materializations(
                records_filter=expected_asset_key, limit=10
            )

            assert all_materializations

            assert dagster_run_id
            dagster_run = dagster_instance.get_run_by_id(dagster_run_id)
            assert dagster_run
            run_ids = dagster_instance.get_run_ids()
            assert dagster_run, f"Could not find dagster run {dagster_run_id} All run_ids {run_ids}"
            assert (
                DAG_RUN_ID_TAG_KEY in dagster_run.tags
            ), f"Could not find dagster run tag: dagster_run.tags {dagster_run.tags}"
            assert (
                dagster_run.tags[DAG_RUN_ID_TAG_KEY] == airflow_run_id
            ), "dagster run tag does not match dag run id"


RAW_METADATA_KEY = "Run Metadata (raw)"


def dag_id_of_mat(event_log_entry: EventLogEntry) -> bool:
    assert event_log_entry.asset_materialization
    assert isinstance(event_log_entry.asset_materialization.metadata, dict)
    json_metadata_value = event_log_entry.asset_materialization.metadata[RAW_METADATA_KEY]
    assert isinstance(json_metadata_value, JsonMetadataValue)
    assert isinstance(json_metadata_value.data, dict)
    return json_metadata_value.data["dag_id"]


def test_dagster_weekly_daily_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that asset orchestrated by two dags loads property. Then
    it triggers both dags that target it, and ensure that two materializations
    register.
    """
    from kitchen_sink.dagster_defs.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    dag_id = "weekly_dag"
    asset_one = AssetKey("asset_one")
    dag_run_id = af_instance.trigger_dag(dag_id=dag_id)
    af_instance.wait_for_run_completion(dag_id=dag_id, run_id=dag_run_id, timeout=60)
    dagster_instance = DagsterInstance.get()

    dag_asset_key = AssetKey(["my_airflow_instance", "dag", dag_id])
    assert poll_for_materialization(dagster_instance, dag_asset_key)
    weekly_mat_event = poll_for_materialization(dagster_instance, asset_one)
    assert weekly_mat_event.asset_materialization
    assert weekly_mat_event.asset_materialization.asset_key == asset_one
    assert dag_id_of_mat(weekly_mat_event) == "weekly_dag"

    dag_id = "daily_dag"
    dag_run_id = af_instance.trigger_dag(dag_id=dag_id)
    af_instance.wait_for_run_completion(dag_id=dag_id, run_id=dag_run_id, timeout=60)

    start_time = get_current_datetime()
    final_result = None
    while get_current_datetime() - start_time < timedelta(seconds=30):
        records_result = dagster_instance.fetch_materializations(records_filter=asset_one, limit=10)

        if len(records_result.records) == 2:
            final_result = records_result
            break

        time.sleep(0.1)

    assert final_result, "Did not get two materializations and timed out"

    assert final_result.records[0].event_log_entry
    assert dag_id_of_mat(final_result.records[0].event_log_entry) == "daily_dag"
    assert dag_id_of_mat(final_result.records[1].event_log_entry) == "weekly_dag"
