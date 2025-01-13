from collections.abc import Mapping
from typing import Optional

from airflow.models.connection import Connection
from airflow.models.dag import DAG
from dagster import (
    ResourceDefinition,
    ScheduleDefinition,
    _check as check,
)
from dagster._utils.schedules import is_valid_cron_schedule

from dagster_airflow.dagster_job_factory import make_dagster_job_from_airflow_dag


def _is_dag_is_schedule(dag: DAG) -> bool:
    cron_schedule = dag.normalized_schedule_interval
    return isinstance(dag.normalized_schedule_interval, str) and is_valid_cron_schedule(
        str(cron_schedule)
    )


def make_dagster_schedule_from_airflow_dag(
    dag: DAG,
    tags: Optional[Mapping[str, str]] = None,
    connections: Optional[list[Connection]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = {},
) -> ScheduleDefinition:
    """Construct a Dagster schedule corresponding to an Airflow DAG.

    Args:
        dag (DAG): Airflow DAG
        tags (Dict[str, Field]): Job tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        connections (List[Connection]): List of Airflow Connections to be created in the Airflow DB

    Returns:
        ScheduleDefinition
    """
    check.inst_param(dag, "dag", DAG)

    cron_schedule = dag.normalized_schedule_interval
    schedule_description = dag.description

    job_def = make_dagster_job_from_airflow_dag(
        dag=dag, tags=tags, connections=connections, resource_defs=resource_defs
    )

    return ScheduleDefinition(
        job=job_def,
        cron_schedule=str(cron_schedule),
        description=schedule_description,
        execution_timezone=dag.timezone.name,
    )
