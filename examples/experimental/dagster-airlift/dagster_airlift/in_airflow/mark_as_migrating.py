import json
import sys

from airflow import DAG
from airflow.models import BaseOperator

from dagster_airlift.in_airflow.dagster_operator import build_dagster_task

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
    dag_vars_to_mark = set()
    task_vars_to_migrate = set()
    all_dags_by_id = {}
    for var, obj in global_vars.items():
        if isinstance(obj, DAG):
            if migration_state.dag_is_being_migrated(obj.dag_id):
                dag_vars_to_mark.add(var)
            all_dags_by_id[obj.dag_id] = obj
        if isinstance(obj, BaseOperator) and migration_state.get_migration_state_for_task(
            dag_id=obj.dag_id, task_id=obj.task_id
        ):
            task_vars_to_migrate.add(var)

    for var in dag_vars_to_mark:
        dag: DAG = global_vars[var]
        print(f"Tagging dag {dag.dag_id} as migrating.")  # noqa: T201
        dag.tags.append(
            json.dumps(
                {"DAGSTER_MIGRATION_STATUS": migration_state.get_migration_dict_for_dag(dag.dag_id)}
            )
        )

    for var in task_vars_to_migrate:
        original_op: BaseOperator = global_vars[var]
        # Need to figure out how to make this constructor resistant to changes in airflow version.
        print(f"Creating new operator for task {original_op.task_id} in dag {original_op.dag_id}")  # noqa: T201
        # First, flush the existing operator from the dag.
        new_op = build_dagster_task(
            task_id=original_op.task_id,
            owner=original_op.owner,
            email=original_op.email,
            email_on_retry=original_op.email_on_retry,
            email_on_failure=original_op.email_on_failure,
            retries=original_op.retries,
            retry_delay=original_op.retry_delay,
            retry_exponential_backoff=original_op.retry_exponential_backoff,
            max_retry_delay=original_op.max_retry_delay,
            start_date=original_op.start_date,
            end_date=original_op.end_date,
            depends_on_past=original_op.depends_on_past,
            wait_for_downstream=original_op.wait_for_downstream,
            params=original_op.params,
            doc_md="This task has been migrated to dagster.",
        )
        original_op.dag.task_dict[original_op.task_id] = new_op

        new_op.upstream_task_ids = original_op.upstream_task_ids
        new_op.downstream_task_ids = original_op.downstream_task_ids
        new_op.dag = original_op.dag
        original_op.dag = None
        print(f"Switching global state var to dagster operator for {var}.")  # noqa: T201
        global_vars[var] = new_op
