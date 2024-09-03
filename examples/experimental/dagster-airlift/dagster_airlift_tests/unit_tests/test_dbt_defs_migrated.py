from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core.dag_defs import dag_defs, task_defs
from dagster_airlift.core.defs_from_airflow import build_defs_from_airflow_instance
from dagster_airlift.dbt import dbt_defs
from dagster_airlift.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
    TaskMigrationState,
)
from dagster_airlift.test import make_instance
from dagster_dbt.dbt_project import DbtProject


def get_dbt_project_path() -> Path:
    return Path(__file__).parent.parent / "integration_tests" / "dbt_project"


def dummy_defs() -> Definitions:
    return Definitions()


def test_dbt_defs() -> None:
    dbt_project_path = get_dbt_project_path()

    dbt_defs_inst = dbt_defs(
        manifest=dbt_project_path / "target" / "manifest.json",
        project=DbtProject(dbt_project_path),
    )

    assert isinstance(dbt_defs_inst, Definitions)

    test_airflow_instance = make_instance(
        dag_and_task_structure={"dag_one": ["task_one"], "dag_two": ["task_two"]}
    )

    initial_defs = Definitions.merge(
        dag_defs(
            "dag_one",
            task_defs("task_one", dbt_defs_inst),
        ),
        dag_defs(
            "dag_two",
            task_defs("task_two", dummy_defs()),
        ),
    )

    assert set((initial_defs.resources or {}).keys()) == {"dbt"}

    defs = build_defs_from_airflow_instance(
        airflow_instance=test_airflow_instance,
        defs=initial_defs,
        migration_state_override=AirflowMigrationState(
            {
                "dag_one": DagMigrationState(
                    {"task_one": TaskMigrationState("task_one", migrated=True)}
                )
            }
        ),
    )

    assert isinstance(defs, Definitions)

    Definitions.validate_loadable(defs)

    assert set(defs.get_repository_def().get_top_level_resources().keys()) == {"dbt"}
