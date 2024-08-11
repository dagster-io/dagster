import json
import logging
from typing import Any, Dict, Optional

from airflow import DAG

from ..migration_state import AirflowMigrationState


def mark_as_dagster_migrating(
    *,
    global_vars: Dict[str, Any],
    migration_state: AirflowMigrationState,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Alters all airflow dags in the current context to be marked as migrating to dagster.
    Uses a migration dictionary to determine the status of the migration for each task within each dag.
    Should only ever be the last line in a dag file.

    Args:
        global_vars (Dict[str, Any]): The global variables in the current context. In most cases, retrieved with `globals()` (no import required).
            This is equivalent to what airflow already does to introspect the dags which exist in a given module context:
            https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#loading-dags
        migration_state (AirflowMigrationState): The migration state for the dags.
        logger (Optional[logging.Logger]): The logger to use. Defaults to logging.getLogger("dagster_airlift").
    """
    caller_module = global_vars.get("__module__")
    suffix = f" in module `{caller_module}`" if caller_module else ""
    if not logger:
        logger = logging.getLogger("dagster_airlift")
    logger.debug(f"Searching for dags migrating to dagster{suffix}...")
    num_dags = 0
    for obj in global_vars.values():
        if not isinstance(obj, DAG):
            continue
        dag: DAG = obj
        logger.debug(f"Checking dag with id `{dag.dag_id}` for migration state.")
        migration_state_for_dag = migration_state.get_migration_dict_for_dag(dag.dag_id)
        if migration_state_for_dag is None:
            logger.debug(
                f"Dag with id `{dag.dag_id} hasn't been marked with migration state. Skipping..."
            )
        else:
            dag.tags.append(json.dumps({"DAGSTER_MIGRATION_STATUS": migration_state_for_dag}))
            logger.debug(
                f"Dag with id `{dag.dag_id}` has been marked with migration state. Adding state to tags for dag."
            )
            num_dags += 1
    logger.info(f"Marked {num_dags} dags as migrating to dagster{suffix}.")
