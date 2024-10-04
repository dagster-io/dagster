import json
import logging
from typing import Any, Dict, List, Optional, Set, Type

from airflow import DAG
from airflow.models import BaseOperator, Variable
from airflow.utils.session import create_session

from dagster_airlift.in_airflow.proxied_state import AirflowProxiedState, DagProxiedState
from dagster_airlift.in_airflow.task_proxy_operator import (
    BaseProxyTaskToDagsterOperator,
    DefaultProxyTaskToDagsterOperator,
    build_dagster_task,
)
from dagster_airlift.utils import get_local_proxied_state_dir


def proxying_to_dagster(
    *,
    global_vars: Dict[str, Any],
    proxied_state: AirflowProxiedState,
    logger: Optional[logging.Logger] = None,
    dagster_operator_klass: Type[
        BaseProxyTaskToDagsterOperator
    ] = DefaultProxyTaskToDagsterOperator,
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
    proxying_dags: List[DAG] = []
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
        for task_id in proxied_state_for_dag.tasks.keys():
            if task_id not in dag.task_dict:
                raise Exception(
                    f"Task with id `{task_id}` not found in dag `{dag.dag_id}`. Found tasks: {list(dag.task_dict.keys())}"
                )
            if not isinstance(dag.task_dict[task_id], BaseOperator):
                raise Exception(
                    f"Task with id `{task_id}` in dag `{dag.dag_id}` is not an instance of BaseOperator. This likely means a MappedOperator was attempted, which is not yet supported by airlift."
                )
        proxying_dags.append(dag)

    if len(all_dag_ids) == 0:
        raise Exception(
            "No dags found in globals dictionary. Ensure that your dags are available from global context, and that the call to `proxying_to_dagster` is the last line in your dag file."
        )

    for dag in proxying_dags:
        logger.debug(f"Tagging dag {dag.dag_id} as proxied.")
        set_proxied_state_for_dag_if_changed(dag.dag_id, proxied_state.dags[dag.dag_id], logger)
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
            new_op = build_dagster_task(original_op, dagster_operator_klass)
            original_op.dag.task_dict[original_op.task_id] = new_op

            new_op.upstream_task_ids = original_op.upstream_task_ids
            new_op.downstream_task_ids = original_op.downstream_task_ids
            new_op.dag = original_op.dag
            original_op.dag = None
            proxied_tasks.add(task_id)
        logger.debug(f"Proxied tasks {proxied_tasks} in dag {dag.dag_id}.")
    logging.debug(f"Proxied {len(proxying_dags)}.")
    logging.debug(f"Completed switching proxied tasks to dagster{suffix}.")


def set_proxied_state_for_dag_if_changed(
    dag_id: str, proxied_state: DagProxiedState, logger: logging.Logger
) -> None:
    if get_local_proxied_state_dir():
        logger.info(
            "Executing in local mode. Not setting proxied state in airflow metadata database, and instead expect dagster to be pointed at proxied state via DAGSTER_AIRLIFT_PROXIED_STATE_DIR env var."
        )
        return
    else:
        prev_proxied_state = get_proxied_state_var_for_dag(dag_id)
        if prev_proxied_state is None or prev_proxied_state != proxied_state:
            logger.info(
                f"Migration state for dag {dag_id} has changed. Setting proxied state in airflow metadata database via Variable."
            )
            set_proxied_state_var_for_dag(dag_id, proxied_state)


def get_proxied_state_var_for_dag(dag_id: str) -> Optional[DagProxiedState]:
    proxied_var = Variable.get(f"{dag_id}_dagster_proxied_state", None)
    if not proxied_var:
        return None
    return DagProxiedState.from_dict(json.loads(proxied_var))


def set_proxied_state_var_for_dag(dag_id: str, proxied_state: DagProxiedState) -> None:
    with create_session() as session:
        Variable.set(
            key=f"{dag_id}_dagster_proxied_state",
            value=json.dumps(proxied_state.to_dict()),
            session=session,
        )
