import logging
from typing import Any, Callable, Dict, List, Optional, Set

from airflow import DAG
from airflow.models import BaseOperator

from dagster_airlift.in_airflow.dag_proxy_operator import (
    BaseProxyDAGToDagsterOperator,
    DefaultProxyDAGToDagsterOperator,
)
from dagster_airlift.in_airflow.proxied_state import AirflowProxiedState
from dagster_airlift.in_airflow.task_proxy_operator import (
    BaseProxyTaskToDagsterOperator,
    DefaultProxyTaskToDagsterOperator,
)


def proxying_to_dagster(
    *,
    global_vars: Dict[str, Any],
    proxied_state: AirflowProxiedState,
    logger: Optional[logging.Logger] = None,
    build_from_task_fn: Callable[
        [BaseOperator], BaseProxyTaskToDagsterOperator
    ] = DefaultProxyTaskToDagsterOperator.build_from_task,
    build_from_dag_fn: Callable[
        [DAG], BaseProxyDAGToDagsterOperator
    ] = DefaultProxyDAGToDagsterOperator.build_from_dag,
) -> None:
    """Uses passed-in dictionary to alter dags and tasks to proxy to dagster.
    Uses a proxied dictionary to determine the proxied status for each task within each dag.
    Should only ever be the last line in a dag file.

    Args:
        global_vars (Dict[str, Any]): The global variables in the current context. In most cases, retrieved with `globals()` (no import required).
            This is equivalent to what airflow already does to introspect the dags which exist in a given module context:
            https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#loading-dags
        proxied_state (AirflowMigrationState): The proxied state for the dags.
        logger (Optional[logging.Logger]): The logger to use. Defaults to logging.getLogger("dagster_airlift").
    """
    caller_module = global_vars.get("__module__")
    suffix = f" in module `{caller_module}`" if caller_module else ""
    if not logger:
        logger = logging.getLogger("dagster_airlift")
    logger.debug(f"Searching for dags proxied to dagster{suffix}...")
    task_level_proxying_dags: List[DAG] = []
    dag_level_proxying_dags: List[DAG] = []
    all_dag_ids: Set[str] = set()
    # Do a pass to collect dags and ensure that proxied information is set correctly.
    for obj in global_vars.values():
        if not isinstance(obj, DAG):
            continue
        dag: DAG = obj
        all_dag_ids.add(dag.dag_id)
        if not proxied_state.dag_has_proxied_state(dag.dag_id):
            logger.debug(f"Dag with id `{dag.dag_id}` has no proxied state. Skipping...")
            continue
        logger.debug(f"Dag with id `{dag.dag_id}` has proxied state.")
        proxied_state_for_dag = proxied_state.dags[dag.dag_id]
        if proxied_state_for_dag.proxied is not None:
            if proxied_state_for_dag.proxied is False:
                logger.debug(f"Dag with id `{dag.dag_id}` is not proxied. Skipping...")
                continue
            dag_level_proxying_dags.append(dag)
        else:
            for task_id in proxied_state_for_dag.tasks.keys():
                if task_id not in dag.task_dict:
                    raise Exception(
                        f"Task with id `{task_id}` not found in dag `{dag.dag_id}`. Found tasks: {list(dag.task_dict.keys())}"
                    )
                if not isinstance(dag.task_dict[task_id], BaseOperator):
                    raise Exception(
                        f"Task with id `{task_id}` in dag `{dag.dag_id}` is not an instance of BaseOperator. This likely means a MappedOperator was attempted, which is not yet supported by airlift."
                    )
            task_level_proxying_dags.append(dag)

    if len(all_dag_ids) == 0:
        raise Exception(
            "No dags found in globals dictionary. Ensure that your dags are available from global context, and that the call to `proxying_to_dagster` is the last line in your dag file."
        )

    for dag in dag_level_proxying_dags:
        logger.debug(f"Tagging dag {dag.dag_id} as proxied.")
        dag.tags = [*dag.tags, "Dag overriden to Dagster"]
        dag.task_dict = {}
        dag.task_group.children = {}
        override_task = build_from_dag_fn(dag)
        dag.task_dict[override_task.task_id] = override_task
    for dag in task_level_proxying_dags:
        logger.debug(f"Tagging dag {dag.dag_id} as proxied.")
        proxied_state_for_dag = proxied_state.dags[dag.dag_id]
        num_proxied_tasks = len(
            [
                task_id
                for task_id, task_state in proxied_state_for_dag.tasks.items()
                if task_state.proxied
            ]
        )
        task_possessive = "Task" if num_proxied_tasks == 1 else "Tasks"
        dag.tags = [
            *dag.tags,
            f"{num_proxied_tasks} {task_possessive} Marked as Proxied to Dagster",
        ]
        proxied_tasks = set()
        for task_id, task_state in proxied_state_for_dag.tasks.items():
            if not task_state.proxied:
                logger.debug(
                    f"Task {task_id} in dag {dag.dag_id} has `proxied` set to False. Skipping..."
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
            new_op = build_from_task_fn(original_op)
            original_op.dag.task_dict[original_op.task_id] = new_op

            new_op.upstream_task_ids = original_op.upstream_task_ids
            new_op.downstream_task_ids = original_op.downstream_task_ids
            new_op.dag = original_op.dag
            original_op.dag = None
            proxied_tasks.add(task_id)
        logger.debug(f"Proxied tasks {proxied_tasks} in dag {dag.dag_id}.")
    logging.debug(f"Proxied {len(task_level_proxying_dags)}.")
    logging.debug(f"Completed switching proxied tasks to dagster{suffix}.")
