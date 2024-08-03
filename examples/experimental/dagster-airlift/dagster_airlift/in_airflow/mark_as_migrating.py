import json
import logging
from typing import Any, Dict, List, Optional

from airflow import DAG
from airflow.models import BaseOperator

from dagster_airlift.in_airflow.dagster_operator import build_dagster_task

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
    migrating_dags: List[DAG] = []
    # Do a pass to collect dags and ensure that migration information is set correctly.
    for obj in global_vars.values():
        if not isinstance(obj, DAG):
            continue
        dag: DAG = obj
        if not migration_state.dag_has_migration_state(dag.dag_id):
            logger.debug(f"Dag with id `{dag.dag_id}` has no migration state. Skipping...")
            continue
        logger.debug(f"Dag with id `{dag.dag_id}` has migration state.")
        migration_state_for_dag = migration_state.dags[dag.dag_id]
        for task_id in migration_state_for_dag.tasks.keys():
            if task_id not in dag.task_dict:
                raise Exception(
                    f"Task with id `{task_id}` not found in dag `{dag.dag_id}`. Found tasks: {list(dag.task_dict.keys())}"
                )
            if not isinstance(dag.task_dict[task_id], BaseOperator):
                raise Exception(
                    f"Task with id `{task_id}` in dag `{dag.dag_id}` is not an instance of BaseOperator. This likely means a MappedOperator was attempted, which is not yet supported by airlift."
                )
        migrating_dags.append(dag)

    for dag in migrating_dags:
        logger.debug(f"Tagging dag {dag.dag_id} as migrating.")
        dag.tags.append(
            json.dumps(
                {"DAGSTER_MIGRATION_STATUS": migration_state.get_migration_dict_for_dag(dag.dag_id)}
            )
        )
        migration_state_for_dag = migration_state.dags[dag.dag_id]
        migrated_tasks = set()
        for task_id, task_state in migration_state_for_dag.tasks.items():
            if not task_state.migrated:
                logger.debug(
                    f"Task {task_id} in dag {dag.dag_id} has `migrated` set to False. Skipping..."
                )
                continue

            # At this point, we should be assured that the task exists within the task_dict of the dag, and is a BaseOperator.
            original_op: BaseOperator = dag.task_dict[task_id]  # type: ignore  # we already confirmed this is BaseOperator
            del dag.task_dict[task_id]
            if original_op.task_group is not None:
                del original_op.task_group.children[task_id]
            logger.debug(
                f"Creating new operator for task {original_op.task_id} in dag {original_op.dag_id}"
            )
            new_op = build_dagster_task(original_op)
            original_op.dag.task_dict[original_op.task_id] = new_op

            new_op.upstream_task_ids = original_op.upstream_task_ids
            new_op.downstream_task_ids = original_op.downstream_task_ids
            new_op.dag = original_op.dag
            original_op.dag = None
            migrated_tasks.add(task_id)
        logger.debug(f"Migrated tasks {migrated_tasks} in dag {dag.dag_id}.")
    logging.debug(f"Migrated {len(migrating_dags)}.")
    logging.debug(f"Completed marking dags and tasks as migrating to dagster{suffix}.")
