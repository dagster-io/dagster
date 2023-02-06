import datetime
import importlib
from typing import AbstractSet, List, Mapping, Optional, Set, Tuple

import airflow
import dateutil
from airflow import __version__ as airflow_version
from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG
from dagster import (
    OpExecutionContext,
    DagsterInvariantViolationError,
    DependencyDefinition,
    In,
    MultiDependencyDefinition,
    Nothing,
    Out,
    RetryPolicy,
    _check as check,
    op,
)
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR

from dagster_airflow.utils import normalized_name, replace_airflow_logger_handlers


def get_graph_definition_args(
    dag,
):
    check.inst_param(dag, "dag", DAG)

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
        )
    return (dependencies, node_defs)


def _traverse_airflow_dag(
    dag: DAG,
    task,
    seen_tasks,
    dependencies,
    node_defs: List[NodeDefinition],
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.list_param(seen_tasks, "seen_tasks", BaseOperator)
    check.list_param(node_defs, "node_defs", NodeDefinition)

    seen_tasks.append(task)
    current_op = make_dagster_op_from_airflow_task(dag=dag, task=task)
    node_defs.append(current_op)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        dependencies[current_op.name] = {
            "airflow_task_ready": MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid=normalized_name(dag_name=dag.dag_id, task_name=task_upstream.task_id),
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
    dag: DAG,
    task: BaseOperator,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)

    @op(
        name=normalized_name(dag_name=dag.dag_id, task_name=task.task_id),
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
        importlib.reload(airflow)
        context.log.info("Running Airflow task: {task_id}".format(task_id=task.task_id))

        if context.has_partition_key:
            # for airflow DAGs that have been turned into SDAs
            execution_date_str = context.pipeline_run.tags.get("dagster/partition")
            execution_date = dateutil.parser.parse(execution_date_str)
            # execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
        else:
            # for airflow DAGs that have not been turned into SDAs
            if AIRFLOW_EXECUTION_DATE_STR not in context.pipeline_run.tags:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to job tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=context.pipeline_run.tags,
                    )
                )
            execution_date_str = context.pipeline_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)
            check.str_param(execution_date_str, "execution_date_str")
            try:
                execution_date = dateutil.parser.parse(execution_date_str)
            except ValueError:
                raise DagsterInvariantViolationError(
                    'Could not parse execution_date "{execution_date_str}". Please use datetime'
                    " format compatible with  dateutil.parser.parse.".format(
                        execution_date_str=execution_date_str,
                    )
                )
            except OverflowError:
                raise DagsterInvariantViolationError(
                    'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'
                    .format(
                        execution_date_str=execution_date_str,
                    )
                )

        check.inst_param(execution_date, "execution_date", datetime.datetime)

        with replace_airflow_logger_handlers():
            if str(airflow_version) >= "2.0.0":
                dag = context.resources.airflow_db["dag"]
                dagrun = context.resources.airflow_db["dagrun"]
                ti = dagrun.get_task_instance(task_id=task.task_id)
                ti.task = dag.get_task(task_id=task.task_id)
                ti.run(ignore_ti_state=True)
            else:
                dag = context.resources.airflow_db["dag"]
                dagrun = context.resources.airflow_db["dagrun"]
                ti = dagrun.get_task_instance(task_id=task.task_id)
                ti.task = dag.get_task(task_id=task.task_id)
                ti.run(ignore_ti_state=True)
            return None

    return _op
