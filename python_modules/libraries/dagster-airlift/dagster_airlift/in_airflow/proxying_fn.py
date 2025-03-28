import logging
from typing import Any, Callable, Optional

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
    global_vars: dict[str, Any],
    proxied_state: AirflowProxiedState,
    logger: Optional[logging.Logger] = None,
    build_from_task_fn: Callable[
        [BaseOperator], BaseProxyTaskToDagsterOperator
    ] = DefaultProxyTaskToDagsterOperator.build_from_task,
    build_from_dag_fn: Callable[
        [DAG], BaseProxyDAGToDagsterOperator
    ] = DefaultProxyDAGToDagsterOperator.build_from_dag,
) -> None:
    """Proxies tasks and dags to Dagster based on provided proxied state.
    Expects a dictionary of in-scope global variables to be provided (typically retrieved with `globals()`), and a proxied state dictionary
    (typically retrieved with :py:func:`load_proxied_state_from_yaml`) for dags in that global state. This function will modify in-place the
    dictionary of global variables to replace proxied tasks with appropriate Dagster operators.

    In the case of task-level proxying, the proxied tasks will be replaced with new operators that are constructed by the provided `build_from_task_fn`.
    A default implementation of this function is provided in `DefaultProxyTaskToDagsterOperator`.
    In the case of dag-level proxying, the entire dag structure will be replaced with a single task that is constructed by the provided `build_from_dag_fn`.
    A default implementation of this function is provided in `DefaultProxyDAGToDagsterOperator`.


    Args:
        global_vars (Dict[str, Any]): The global variables in the current context. In most cases, retrieved with `globals()` (no import required).
            This is equivalent to what airflow already does to introspect the dags which exist in a given module context:
            https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#loading-dags
        proxied_state (AirflowMigrationState): The proxied state for the dags.
        logger (Optional[logging.Logger]): The logger to use. Defaults to logging.getLogger("dagster_airlift").


    Examples:
        Typical usage of this function is to be called at the end of a dag file, retrieving proxied_state from an accompanying `proxied_state` path.

        .. code-block:: python

            from pathlib import Path

            from airflow import DAG
            from airflow.operators.python import PythonOperator
            from dagster._time import get_current_datetime_midnight
            from dagster_airlift.in_airflow import proxying_to_dagster
            from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


            with DAG(
                dag_id="daily_interval_dag",
                ...,
            ) as minute_dag:
                PythonOperator(task_id="my_task", python_callable=...)

            # At the end of the dag file, so we can ensure dags are loaded into globals.
            proxying_to_dagster(
                proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
                global_vars=globals(),
            )

        You can also provide custom implementations of the `build_from_task_fn` function to customize the behavior of task-level proxying.

        .. code-block:: python

            from dagster_airlift.in_airflow import proxying_to_dagster, BaseProxyTaskToDagsterOperator
            from airflow.models.operator import BaseOperator

            ... # Dag code here

            class CustomAuthTaskProxyOperator(BaseProxyTaskToDagsterOperator):
                def get_dagster_session(self, context: Context) -> requests.Session:
                    # Add custom headers to the session
                    return requests.Session(headers={"Authorization": "Bearer my_token"})

                def get_dagster_url(self, context: Context) -> str:
                    # Use a custom environment variable for the dagster url
                    return os.environ["CUSTOM_DAGSTER_URL"]

                @classmethod
                def build_from_task(cls, task: BaseOperator) -> "CustomAuthTaskProxyOperator":
                    # Custom logic to build the operator from the task (task_id should remain the same)
                    if task.task_id == "my_task_needs_more_retries":
                        return CustomAuthTaskProxyOperator(task_id=task_id, retries=3)
                    else:
                        return CustomAuthTaskProxyOperator(task_id=task_id)

            proxying_to_dagster(
                proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
                global_vars=globals(),
                build_from_task_fn=CustomAuthTaskProxyOperator.build_from_task,
            )

        You can do the same for dag-level proxying by providing a custom implementation of the `build_from_dag_fn` function.

        .. code-block:: python

            from dagster_airlift.in_airflow import proxying_to_dagster, BaseProxyDAGToDagsterOperator
            from airflow.models.dag import DAG

            ... # Dag code here

            class CustomAuthDAGProxyOperator(BaseProxyDAGToDagsterOperator):
                def get_dagster_session(self, context: Context) -> requests.Session:
                    # Add custom headers to the session
                    return requests.Session(headers={"Authorization": "Bearer my_token"})

                def get_dagster_url(self, context: Context) -> str:
                    # Use a custom environment variable for the dagster url
                    return os.environ["CUSTOM_DAGSTER_URL"]

                @classmethod
                def build_from_dag(cls, dag: DAG) -> "CustomAuthDAGProxyOperator":
                    # Custom logic to build the operator from the dag (DAG id should remain the same)
                    if dag.dag_id == "my_dag_needs_more_retries":
                        return CustomAuthDAGProxyOperator(task_id="custom override", retries=3, dag=dag)
                    else:
                        return CustomAuthDAGProxyOperator(task_id="basic_override", dag=dag)

            proxying_to_dagster(
                proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
                global_vars=globals(),
                build_from_dag_fn=CustomAuthDAGProxyOperator.build_from_dag,
            )

    """
    caller_module = global_vars.get("__module__")
    suffix = f" in module `{caller_module}`" if caller_module else ""
    if not logger:
        logger = logging.getLogger("dagster_airlift")
    logger.debug(f"Searching for dags proxied to dagster{suffix}...")
    task_level_proxying_dags: list[DAG] = []
    dag_level_proxying_dags: list[DAG] = []
    all_dag_ids: set[str] = set()
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
