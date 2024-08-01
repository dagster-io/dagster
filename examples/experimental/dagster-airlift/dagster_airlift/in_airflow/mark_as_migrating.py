import json
import sys

from airflow import DAG

from ..migration_state import AirflowMigrationState


def mark_as_dagster_migrating(
    migration_state: AirflowMigrationState,
) -> None:
    """Alters all airflow dags in the current context to be marked as migrating to dagster.
    Uses a migration dictionary to determine the status of the migration for each task within each dag.
    Should only ever be the last line in a dag file.
    """
    # get global context from above frame
    global_vars = sys._getframe(1).f_globals  # noqa: SLF001

    any_dags_marked = False
    for obj in global_vars.values():
        if not isinstance(obj, DAG):
            continue
        dag: DAG = obj
        migration_status = migration_state.get_migration_dict_for_dag(dag.dag_id)
        # If there are migrated tasks, then add a tag to the dag to indicate that it is migrating.
        if migration_status is not None:
            any_dags_marked = True
            dag.tags.append(json.dumps({"DAGSTER_MIGRATION_STATUS": migration_status}))

    if not any_dags_marked:
        # Should we warn here?
        raise Exception(
            "No dags were marked as migrating. This is likely an error in the migration state file."
        )
