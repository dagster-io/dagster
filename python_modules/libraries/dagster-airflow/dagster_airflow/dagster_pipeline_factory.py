from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG

from dagster import (
    DependencyDefinition,
    InputDefinition,
    MultiDependencyDefinition,
    Nothing,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    solid,
)


def make_dagster_pipeline_from_airflow_dag(dag):
    check.inst_param(dag, 'dag', DAG)

    pipeline_dependencies, solid_defs = _get_pipeline_definition_args(dag)
    pipelineDefinition = PipelineDefinition(
        name='airflow_' + dag.dag_id, solid_defs=solid_defs, dependencies=pipeline_dependencies,
    )
    return pipelineDefinition


def _get_pipeline_definition_args(dag):
    check.inst_param(dag, 'dag', DAG)
    pipeline_dependencies = {}
    solid_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(task, seen_tasks, pipeline_dependencies, solid_defs)
    return (pipeline_dependencies, solid_defs)


def _traverse_airflow_dag(task, seen_tasks, pipeline_dependencies, solid_defs):
    check.inst_param(task, 'task', BaseOperator)
    check.list_param(seen_tasks, 'seen_tasks', BaseOperator)
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)

    seen_tasks.append(task)
    current_solid = make_dagster_solid_from_airflow_task(task)
    solid_defs.append(current_solid)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        pipeline_dependencies[current_solid.name] = {
            'airflow_task_ready': MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid='airflow_' + task_upstream.task_id, output='airflow_task_complete'
                    )
                    for task_upstream in task_upstream_list
                ]
            )
        }

    # To enforce predictable iteration order
    task_downstream_list = sorted(task.downstream_list, key=lambda x: x.task_id)
    for child_task in task_downstream_list:
        if child_task not in seen_tasks:
            _traverse_airflow_dag(child_task, seen_tasks, pipeline_dependencies, solid_defs)


def make_dagster_solid_from_airflow_task(task):
    check.inst_param(task, 'task', BaseOperator)

    @solid(
        name='airflow_' + task.task_id,
        input_defs=[InputDefinition('airflow_task_ready', Nothing)],
        output_defs=[OutputDefinition(Nothing, 'airflow_task_complete')],
    )
    def _solid(context):  # pylint: disable=unused-argument
        # Todo: add inner execution
        return None

    return _solid
