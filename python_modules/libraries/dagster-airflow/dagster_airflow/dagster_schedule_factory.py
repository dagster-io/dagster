from airflow.models.dag import DAG
from dagster import (
    JobDefinition,
    ScheduleDefinition,
    _check as check,
)
from dagster._utils.schedules import is_valid_cron_schedule


# pylint: enable=no-name-in-module,import-error
def make_dagster_schedule_from_airflow_dag(dag: DAG, job_def: JobDefinition):
    """Construct a Dagster schedule corresponding to an Airflow DAG.

    Args:
        dag (DAG): Airflow DAG
        job_def (JobDefinition): Dagster pipeline corresponding to Airflow DAG
    Returns:
        ScheduleDefinition
    """
    check.inst_param(dag, "dag", DAG)
    check.inst_param(job_def, "job_def", JobDefinition)

    cron_schedule = dag.normalized_schedule_interval
    schedule_description = dag.description

    if isinstance(dag.normalized_schedule_interval, str) and is_valid_cron_schedule(
        str(cron_schedule)
    ):
        return ScheduleDefinition(
            job=job_def,
            cron_schedule=str(cron_schedule),
            description=schedule_description,
            execution_timezone=dag.timezone.name,
        )
