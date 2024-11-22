import os
import subprocess
import time
from datetime import timedelta
from pathlib import Path
from typing import Generator, List, Mapping, NamedTuple, Sequence, Union

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.events.log import EventLogEntry
from dagster._core.test_utils import environ
from dagster._time import get_current_datetime
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.test.shared_fixtures import stand_up_airflow


def makefile_dir() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir(), check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir() / ".airflow_home"),
            "DAGSTER_HOME": str(makefile_dir() / ".dagster_home"),
        }
    ):
        yield
    subprocess.run(["make", "wipe"], cwd=makefile_dir(), check=True)


@pytest.fixture(name="dags_dir")
def dags_dir_fixture() -> Path:
    return makefile_dir() / "kitchen_sink" / "airflow_dags"


@pytest.fixture(name="airflow_home")
def airflow_home_fixture(local_env: None) -> Path:
    return Path(os.environ["AIRFLOW_HOME"])


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_airflow"], env=os.environ, cwd=makefile_dir()
    ) as process:
        yield process


def poll_for_airflow_run_existence_and_completion(
    af_instance: AirflowInstance, dag_id: str, af_run_id: str, duration: int
) -> None:
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            af_instance.wait_for_run_completion(
                dag_id=dag_id, run_id=af_run_id, timeout=int(time.time() - start_time)
            )
            return
        # Run may not exist yet
        except Exception:
            time.sleep(0.1)
            continue


class ExpectedMat(NamedTuple):
    asset_key: AssetKey
    runs_in_dagster: bool


def poll_for_expected_mats(
    af_instance: AirflowInstance,
    expected_mats_per_dag: Mapping[str, Sequence[Union[ExpectedMat, AssetKey]]],
) -> None:
    resolved_expected_mats_per_dag: Mapping[str, list[ExpectedMat]] = {
        dag_id: [
            expected_mat
            if isinstance(expected_mat, ExpectedMat)
            else ExpectedMat(expected_mat, True)
            for expected_mat in expected_mats
        ]
        for dag_id, expected_mats in expected_mats_per_dag.items()
    }
    for dag_id, expected_mats in resolved_expected_mats_per_dag.items():
        airflow_run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=airflow_run_id, timeout=60)
        dagster_instance = DagsterInstance.get()

        dag_asset_key = AssetKey([af_instance.name, "dag", dag_id])
        assert poll_for_materialization(dagster_instance, dag_asset_key)

        for expected_mat in expected_mats:
            mat_event_log_entry = poll_for_materialization(dagster_instance, expected_mat.asset_key)
            assert mat_event_log_entry.asset_materialization
            assert mat_event_log_entry.asset_materialization.asset_key == expected_mat.asset_key

            assert mat_event_log_entry.asset_materialization
            dagster_run_id = mat_event_log_entry.run_id

            all_materializations = dagster_instance.fetch_materializations(
                records_filter=expected_mat.asset_key, limit=10
            )

            assert all_materializations

            if expected_mat.runs_in_dagster:
                assert dagster_run_id
                dagster_run = dagster_instance.get_run_by_id(dagster_run_id)
                assert dagster_run
                run_ids = dagster_instance.get_run_ids()
                assert (
                    dagster_run
                ), f"Could not find dagster run {dagster_run_id} All run_ids {run_ids}"
                assert (
                    DAG_RUN_ID_TAG_KEY in dagster_run.tags
                ), f"Could not find dagster run tag: dagster_run.tags {dagster_run.tags}"
                assert (
                    dagster_run.tags[DAG_RUN_ID_TAG_KEY] == airflow_run_id
                ), "dagster run tag does not match dag run id"


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
