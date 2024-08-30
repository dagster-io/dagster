import contextlib
import importlib
from pathlib import Path
from typing import AbstractSet, Callable, Iterable, Optional

import pytest
from dagster import DagsterInstance
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster_airlift.core import AirflowInstance, BasicAuthBackend
from dagster_airlift.core.utils import MIGRATED_TAG, TASK_ID_TAG

from .utils import (
    poll_for_materialization,
    start_run_and_wait_for_completion,
    wait_for_all_runs_to_complete,
)


def _assert_dagster_migration_states_are(
    state: bool, where: Optional[Callable[[AssetSpec], bool]] = None
) -> None:
    """Loads the Dagster asset definitions and checks that all asset specs have the correct migration state.

    This is a helper function so that we can call this as many times as we need to - if there are dangling references
    to any of the imports from the module, the importlib.reload won't work properly.

    Args:
        state: The expected migration state.
        where: A function that takes an AssetSpec and returns True if the spec should be checked, False otherwise.
    """
    import tutorial_example
    from tutorial_example.dagster_defs.stages import migrate
    from tutorial_example.dagster_defs.stages.migrate import defs

    importlib.reload(tutorial_example)
    importlib.reload(migrate)

    assert defs
    specs = defs.get_all_asset_specs()
    spec_migration_states = {
        spec.key: spec.tags.get(MIGRATED_TAG) for spec in specs if not where or where(spec)
    }

    assert all(
        value == str(state)
        for key, value in spec_migration_states.items()
        if key.path[0] != "airflow_instance"  # ignore overall dag, which doesn't have tag
    ), str(spec_migration_states)


@pytest.mark.skip(reason="Flakiness, @benpankow to investigate")
def test_migration_status(
    airflow_instance,
    mark_tasks_migrated: Callable[[AbstractSet[str]], contextlib.AbstractContextManager],
) -> None:
    """Iterates through various combinations of marking tasks as migrated and checks that the migration state is updated correctly in
    both the Airflow DAGs and the Dagster asset definitions.
    """
    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    )

    with mark_tasks_migrated(set()):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]
        assert dag.dag_id == "rebuild_customers_list"
        assert not dag.migration_state.is_task_migrated("load_raw_customers")
        assert not dag.migration_state.is_task_migrated("build_dbt_models")
        assert not dag.migration_state.is_task_migrated("export_customers")

        _assert_dagster_migration_states_are(False)

    with mark_tasks_migrated({"load_raw_customers"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]

        assert dag.dag_id == "rebuild_customers_list"
        assert dag.migration_state.is_task_migrated("load_raw_customers")
        assert not dag.migration_state.is_task_migrated("build_dbt_models")
        assert not dag.migration_state.is_task_migrated("export_customers")

        _assert_dagster_migration_states_are(
            True, where=lambda spec: spec.tags.get(TASK_ID_TAG) == "load_raw_customers"
        )
        _assert_dagster_migration_states_are(
            False, where=lambda spec: spec.tags.get(TASK_ID_TAG) != "load_raw_customers"
        )

    with mark_tasks_migrated({"build_dbt_models"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]
        assert dag.dag_id == "rebuild_customers_list"
        assert not dag.migration_state.is_task_migrated("load_raw_customers")
        assert dag.migration_state.is_task_migrated("build_dbt_models")
        assert not dag.migration_state.is_task_migrated("export_customers")

        _assert_dagster_migration_states_are(
            True, where=lambda spec: spec.tags.get(TASK_ID_TAG) == "build_dbt_models"
        )
        _assert_dagster_migration_states_are(
            False, where=lambda spec: spec.tags.get(TASK_ID_TAG) != "build_dbt_models"
        )

    with mark_tasks_migrated({"load_raw_customers", "build_dbt_models", "export_customers"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]
        assert dag.dag_id == "rebuild_customers_list"
        assert dag.migration_state.is_task_migrated("load_raw_customers")
        assert dag.migration_state.is_task_migrated("build_dbt_models")
        assert dag.migration_state.is_task_migrated("export_customers")

        _assert_dagster_migration_states_are(True)


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(
    makefile_dir: Path,
    airflow_instance: None,
    local_env,
    mark_tasks_migrated: Callable[[AbstractSet[str]], contextlib.AbstractContextManager],
) -> Iterable[str]:
    # Mark only the build_dbt_models task as migrated
    with mark_tasks_migrated({"load_raw_customers", "build_dbt_models", "export_customers"}):
        yield str(makefile_dir / "tutorial_example" / "dagster_defs" / "stages" / "migrate.py")


@pytest.mark.skip(reason="Flakiness, @benpankow to investigate")
def test_migrate_runs_properly_in_dagster(airflow_instance: None, dagster_dev: None) -> None:
    instance = DagsterInstance.get()

    from tutorial_example.dagster_defs.stages.migrate import defs

    all_keys = [spec.key for spec in defs.get_all_asset_specs()]
    assert len(all_keys) == 10

    mat_events = instance.get_latest_materialization_events(asset_keys=all_keys)
    for key, event in mat_events.items():
        assert event is None, f"Materialization event for {key} is not None"

    start_run_and_wait_for_completion("rebuild_customers_list")

    poll_for_materialization(instance, target=all_keys)

    # Ensure migrated tasks are run in Dagster
    wait_for_all_runs_to_complete(instance)
    runs = instance.get_runs()
    assert len(runs) == 1
    # Ensure just the dbt assets ran (7 assets)
    assert runs[0].asset_selection and len(runs[0].asset_selection) == 7
    assert runs[0].status == DagsterRunStatus.SUCCESS
