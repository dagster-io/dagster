import importlib

import airflow
from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG
from dagster import (
    DependencyDefinition,
    In,
    MultiDependencyDefinition,
    Nothing,
    OpExecutionContext,
    Out,
    RetryPolicy,
    _check as check,
    op,
)
from dagster._core.definitions.node_definition import NodeDefinition

from dagster_airflow.utils import is_airflow_2, normalized_name, replace_airflow_logger_handlers


def get_graph_definition_args(
    dag,
    unique_id=None,
):
    check.inst_param(dag, "dag", DAG)
    unique_id = check.opt_int_param(unique_id, "unique_id")

    dependencies = {}
    node_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(
            dag=dag,
            task=task,
            seen_tasks=seen_tasks,
            dependencies=dependencies,
            node_defs=node_defs,
            unique_id=unique_id,
        )
    return (dependencies, node_defs)


def _traverse_airflow_dag(
    dag,
    task,
    seen_tasks,
    dependencies,
    node_defs,
    unique_id,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.list_param(seen_tasks, "seen_tasks", BaseOperator)
    check.list_param(node_defs, "node_defs", NodeDefinition)
    unique_id = check.opt_int_param(unique_id, "unique_id")

    seen_tasks.append(task)
    current_op = make_dagster_op_from_airflow_task(
        dag=dag,
        task=task,
        unique_id=unique_id,
    )
    node_defs.append(current_op)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        dependencies[current_op.name] = {
            "airflow_task_ready": MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid=normalized_name(task_upstream.task_id, unique_id),
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
                unique_id=unique_id,
            )


# If unique_id is not None, this id will be postpended to generated solid names, generally used
# to enforce unique solid names within a repo.
def make_dagster_op_from_airflow_task(
    dag,
    task,
    unique_id=None,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    unique_id = check.opt_int_param(unique_id, "unique_id")

    @op(
        name=normalized_name(task.task_id, unique_id),
        required_resource_keys={"airflow_db"},
        ins={"airflow_task_ready": In(Nothing)},
        out={"airflow_task_complete": Out(Nothing)},
        retry_policy=RetryPolicy(
            max_retries=task.retries if task.retries is not None else 0,
            delay=task.retry_delay.total_seconds() if task.retry_delay is not None else 0,
        ),
    )
    def _op(context: OpExecutionContext):  # pylint: disable=unused-argument
        # reloading forces picking up any config that's been set for execution
        if is_airflow_2():
            importlib.reload(airflow.configuration)
            importlib.reload(airflow.settings)
            importlib.reload(airflow)
        else:
            importlib.reload(airflow)
        context.log.info("Running Airflow task: {task_id}".format(task_id=task.task_id))

        with replace_airflow_logger_handlers():
            dag = context.resources.airflow_db["dag"]
            dagrun = context.resources.airflow_db["dagrun"]
            ti = dagrun.get_task_instance(task_id=task.task_id)
            ti.task = dag.get_task(task_id=task.task_id)
            ti.run(ignore_ti_state=True)

    return _op
