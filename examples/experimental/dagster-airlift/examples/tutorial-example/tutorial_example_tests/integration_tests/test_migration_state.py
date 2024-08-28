import contextlib
import importlib
from typing import AbstractSet, Callable

from dagster_airlift.core import AirflowInstance, BasicAuthBackend
from dagster_airlift.core.utils import MIGRATED_TAG


def test_migration_status(
    airflow_instance,
    mark_tasks_migrated: Callable[[AbstractSet[str]], contextlib.AbstractContextManager],
) -> None:
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

        import tutorial_example
        from tutorial_example.dagster_defs.definitions import defs

        assert defs
        specs = defs.get_all_asset_specs()

        assert all(spec.tags.get(MIGRATED_TAG) in (None, "False") for spec in specs)

    with mark_tasks_migrated({"load_raw_customers"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]

        assert dag.dag_id == "rebuild_customers_list"
        assert dag.migration_state.is_task_migrated("load_raw_customers")
        assert not dag.migration_state.is_task_migrated("build_dbt_models")
        assert not dag.migration_state.is_task_migrated("export_customers")

    with mark_tasks_migrated({"build_dbt_models"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]
        assert dag.dag_id == "rebuild_customers_list"
        assert not dag.migration_state.is_task_migrated("load_raw_customers")
        assert dag.migration_state.is_task_migrated("build_dbt_models")
        assert not dag.migration_state.is_task_migrated("export_customers")

    with mark_tasks_migrated({"load_raw_customers", "build_dbt_models", "export_customers"}):
        assert len(instance.list_dags()) == 1
        dag = instance.list_dags()[0]
        assert dag.dag_id == "rebuild_customers_list"
        assert dag.migration_state.is_task_migrated("load_raw_customers")
        assert dag.migration_state.is_task_migrated("build_dbt_models")
        assert dag.migration_state.is_task_migrated("export_customers")

        importlib.reload(tutorial_example)

        assert defs
        specs = defs.get_all_asset_specs()

        assert all(spec.tags.get(MIGRATED_TAG) in (None, "True") for spec in specs)
