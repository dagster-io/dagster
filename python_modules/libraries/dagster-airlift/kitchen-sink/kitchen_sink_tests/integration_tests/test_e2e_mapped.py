import time
from datetime import timedelta
from typing import List

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._time import get_current_datetime, get_current_datetime_midnight

from kitchen_sink_tests.integration_tests.conftest import (
    makefile_dir,
    poll_for_airflow_run_existence_and_completion,
    poll_for_expected_mats,
    poll_for_materialization,
)


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> list[str]:
    return ["make", "run_dagster_mapped", "-C", str(makefile_dir())]


def test_migrated_dagster_print_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that materializations register."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_mats_per_dag = {
        "print_dag": [AssetKey("print_asset")],
    }

    poll_for_expected_mats(af_instance, expected_mats_per_dag)


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
    from kitchen_sink.airflow_instance import local_airflow_instance

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


def test_migrated_overridden_dag_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets are properly materialized from an overridden dag."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_mats_per_dag = {
        "overridden_dag": [AssetKey("asset_two")],
    }
    poll_for_expected_mats(af_instance, expected_mats_per_dag)


def test_custom_callback_behavior(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that custom callbacks to proxying_to_dagster are properly applied."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_mats_per_dag = {
        "affected_dag": [
            AssetKey("affected_dag__print_asset"),
            AssetKey("affected_dag__another_print_asset"),
        ],
        "unaffected_dag": [
            AssetKey("unaffected_dag__print_asset"),
            AssetKey("unaffected_dag__another_print_asset"),
        ],
    }

    poll_for_expected_mats(af_instance, expected_mats_per_dag)

    for task_id in ["print_task", "downstream_print_task"]:
        affected_print_task = af_instance.get_task_info(dag_id="affected_dag", task_id=task_id)
        assert affected_print_task.metadata["retries"] == 1
        unaffected_print_task = af_instance.get_task_info(dag_id="unaffected_dag", task_id=task_id)
        assert unaffected_print_task.metadata["retries"] == 0


def test_migrated_overridden_dag_custom_operator_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets are properly materialized from an overridden dag, and that the proxied task retains attributes from the custom operator."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()
    assert af_instance.get_task_info(dag_id="overridden_dag_custom_callback", task_id="OVERRIDDEN")

    expected_mats_per_dag = {
        "overridden_dag_custom_callback": [AssetKey("asset_overridden_dag_custom_callback")],
    }
    poll_for_expected_mats(af_instance, expected_mats_per_dag)


def test_partitioned_observation(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets with time-window partitions get partitions mapped correctly onto their materializations."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()
    af_run_id = af_instance.trigger_dag(
        dag_id="daily_interval_dag", logical_date=get_current_datetime_midnight()
    )
    af_instance.wait_for_run_completion(dag_id="daily_interval_dag", run_id=af_run_id, timeout=30)

    dagster_instance = DagsterInstance.get()
    entry = poll_for_materialization(
        dagster_instance=dagster_instance,
        asset_key=AssetKey("daily_interval_dag__partitioned"),
    )
    assert entry.asset_materialization
    assert entry.asset_materialization.partition


def test_assets_multiple_jobs_same_task(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test the case where multiple assets within the same task have different jobs. Ensure we still materialize them correctly."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()
    assert af_instance.get_task_info(dag_id="overridden_dag_custom_callback", task_id="OVERRIDDEN")

    expected_mats_per_dag = {
        "multi_job_assets_dag": [
            AssetKey("multi_job__a"),
            AssetKey("multi_job__b"),
            AssetKey("multi_job__c"),
        ],
    }
    poll_for_expected_mats(af_instance, expected_mats_per_dag)


def test_partitioned_migrated(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that partitioned assets are properly materialized from a proxied task."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()
    af_instance.unpause_dag(dag_id="migrated_daily_interval_dag")
    # Wait for dag run to exist
    expected_logical_date = get_current_datetime_midnight() - timedelta(days=1)
    expected_run_id = f"scheduled__{expected_logical_date.isoformat()}"
    poll_for_airflow_run_existence_and_completion(
        af_instance=af_instance,
        dag_id="migrated_daily_interval_dag",
        af_run_id=expected_run_id,
        duration=30,
    )
    dagster_instance = DagsterInstance.get()
    entry = poll_for_materialization(
        dagster_instance=dagster_instance,
        asset_key=AssetKey("migrated_daily_interval_dag__partitioned"),
    )
    assert entry.asset_materialization
    assert entry.asset_materialization.partition
    assert entry.asset_materialization.partition == expected_logical_date.strftime("%Y-%m-%d")
