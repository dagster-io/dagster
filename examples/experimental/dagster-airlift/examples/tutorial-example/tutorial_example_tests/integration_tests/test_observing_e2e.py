from pathlib import Path

import pytest
from dagster import DagsterInstance

from .utils import poll_for_materialization, start_run_and_wait_for_completion


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(
    makefile_dir: Path,
    local_env,
) -> str:
    return str(makefile_dir / "tutorial_example" / "dagster_defs" / "stages" / "observe.py")


@pytest.mark.skip(reason="Flakiness, @benpankow to investigate")
def test_observe_reflects_dag_completion_status(airflow_instance: None, dagster_dev: None) -> None:
    instance = DagsterInstance.get()

    from tutorial_example.dagster_defs.stages.observe import defs

    all_keys = [spec.key for spec in defs.get_all_asset_specs()]
    assert len(all_keys) == 10

    mat_events = instance.get_latest_materialization_events(asset_keys=all_keys)
    for key, event in mat_events.items():
        assert event is None, f"Materialization event for {key} is not None"

    start_run_and_wait_for_completion("rebuild_customers_list")

    poll_for_materialization(instance, target=all_keys)
