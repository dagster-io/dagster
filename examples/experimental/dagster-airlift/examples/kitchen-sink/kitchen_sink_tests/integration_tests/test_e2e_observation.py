import os
import time
from datetime import timedelta
from typing import List

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._time import get_current_datetime

from kitchen_sink_tests.integration_tests.conftest import makefile_dir

RAW_METADATA_KEY = "Run Metadata (raw)"


def dag_id_of_mat(event_log_entry: EventLogEntry) -> bool:
    assert event_log_entry.asset_materialization
    assert isinstance(event_log_entry.asset_materialization.metadata, dict)
    json_metadata_value = event_log_entry.asset_materialization.metadata[RAW_METADATA_KEY]
    assert isinstance(json_metadata_value, JsonMetadataValue)
    assert isinstance(json_metadata_value.data, dict)
    return json_metadata_value.data["dag_id"]


def poll_for_observation(
    dagster_instance: DagsterInstance,
    asset_key: AssetKey,
) -> EventLogEntry:
    start_time = get_current_datetime()
    while get_current_datetime() - start_time < timedelta(seconds=30):
        records = dagster_instance.fetch_observations(records_filter=asset_key, limit=1).records
        if len(records) > 0:
            return records[0].event_log_entry
        time.sleep(0.1)

    raise Exception(f"Timeout waiting for observation event on {asset_key}")


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> List[str]:
    return ["make", "run_observation_defs", "-C", str(makefile_dir())]


def test_observation_defs_are_observed(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that observations register."""
    from kitchen_sink.dagster_defs.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_obs_per_dag = {
        "simple_unproxied_dag": [AssetKey("my_asset"), AssetKey("my_downstream_asset")],
    }

    for dag_id, expected_asset_keys in expected_obs_per_dag.items():
        airflow_run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=airflow_run_id, timeout=60)
        dagster_instance = DagsterInstance.get()

        dag_asset_key = AssetKey(["my_airflow_instance", "dag", dag_id])
        assert poll_for_observation(dagster_instance, dag_asset_key)

        for expected_asset_key in expected_asset_keys:
            obs_entry = poll_for_observation(dagster_instance, expected_asset_key)
            assert obs_entry.asset_observation
            assert obs_entry.asset_observation.asset_key == expected_asset_key
