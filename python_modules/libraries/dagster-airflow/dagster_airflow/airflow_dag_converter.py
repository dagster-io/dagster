import importlib
from typing import TYPE_CHECKING

import airflow
from airflow.models.dag import DAG
from dagster import (
    DependencyDefinition,
    In,
    MultiDependencyDefinition,
    Nothing,
    OpDefinition,
    OpExecutionContext,
    Out,
    RetryPolicy,
    _check as check,
    op,
)
from dagster._core.definitions.node_definition import NodeDefinition

from dagster_airflow.utils import (
    is_airflow_2_loaded_in_environment,
    normalized_name,
    replace_airflow_logger_handlers,
)

if TYPE_CHECKING:
    from airflow.models.baseoperator import BaseOperator


def get_graph_definition_args(
    dag: DAG,
):
    check.inst_param(dag, "dag", DAG)

    dependencies: dict[str, dict[str, MultiDependencyDefinition]] = {}
    node_defs: list[NodeDefinition] = []
    seen_tasks: list[BaseOperator] = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(
            dag=dag,
            task=task,
            seen_tasks=seen_tasks,
            dependencies=dependencies,
            node_defs=node_defs,
        )
    return (dependencies, node_defs)


def _traverse_airflow_dag(dag, task, seen_tasks, dependencies, node_defs):
    check.inst_param(dag, "dag", DAG)
    check.list_param(node_defs, "node_defs", NodeDefinition)

    seen_tasks.append(task)
    current_op = make_dagster_op_from_airflow_task(
        dag=dag,
        task=task,
    )
    node_defs.append(current_op)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        dependencies[current_op.name] = {
            "airflow_task_ready": MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        node=normalized_name(dag.dag_id, task_upstream.task_id),
                        output="airflow_task_complete",
                    )
                    for task_upstream in task_upstream_list
                ]
            )
        }

    # To enforce predictable iteration order
    task_downstream_list = sorted(task.downstream_list, key=lambda x: x.task_id)
    for child_task in task_downstream_list:
        if child_task not in seen_tasks:
            _traverse_airflow_dag(
                dag=dag,
                task=child_task,
                seen_tasks=seen_tasks,
                dependencies=dependencies,
                node_defs=node_defs,
            )


def make_dagster_op_from_airflow_task(
    dag,
    task,
) -> OpDefinition:
    check.inst_param(dag, "dag", DAG)

    @op(
        name=normalized_name(dag.dag_id, task.task_id),
        required_resource_keys={"airflow_db"},
        ins={"airflow_task_ready": In(Nothing)},
        out={"airflow_task_complete": Out(Nothing)},
        retry_policy=RetryPolicy(
            max_retries=task.retries if task.retries is not None else 0,
            delay=task.retry_delay.total_seconds() if task.retry_delay is not None else 0,
        ),
    )
    def _op(context: OpExecutionContext):
        # reloading forces picking up any config that's been set for execution
        if is_airflow_2_loaded_in_environment():
            importlib.reload(airflow.configuration)
            importlib.reload(airflow.settings)
            importlib.reload(airflow)
        else:
            importlib.reload(airflow)
        context.log.info(f"Running Airflow task: {task.task_id}")

        with replace_airflow_logger_handlers():
            dagrun = context.resources.airflow_db.get_dagrun(dag=dag)
            ti = dagrun.get_task_instance(task_id=task.task_id)
            ti.task = dag.get_task(task_id=task.task_id)
            ti.run(ignore_ti_state=True)

    return _op
