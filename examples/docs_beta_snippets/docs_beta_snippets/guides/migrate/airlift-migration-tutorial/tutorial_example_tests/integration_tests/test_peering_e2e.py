from pathlib import Path

import pytest
from dagster import AssetKey, DagsterInstance

from .utils import poll_for_materialization, start_run_and_wait_for_completion


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(
    makefile_dir: Path,
    local_env,
) -> str:
    return str(makefile_dir / "tutorial_example" / "dagster_defs" / "stages" / "peer.py")


@pytest.mark.skip(reason="Flakiness, @benpankow to investigate")
def test_peer_reflects_dag_completion_status(airflow_instance: None, dagster_dev: None) -> None:
    instance = DagsterInstance.get()

    mat_event = instance.get_latest_materialization_event(
        AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"])
    )
    assert mat_event is None

    start_run_and_wait_for_completion("rebuild_customers_list")

    poll_for_materialization(
        instance, target=AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"])
    )
