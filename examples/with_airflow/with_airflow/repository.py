import os
from datetime import datetime

from airflow.models import DagBag
from dagster import repository

# start_repo_marker_0
from dagster_airflow import (
    make_dagster_job_from_airflow_dag,
    make_schedules_and_jobs_from_airflow_dag_bag,
)

from with_airflow.airflow_complex_dag import complex_dag
from with_airflow.airflow_kubernetes_dag import kubernetes_dag
from with_airflow.airflow_simple_dag import simple_dag

airflow_simple_dag = make_dagster_job_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_job_from_airflow_dag(complex_dag)
airflow_kubernetes_dag = make_dagster_job_from_airflow_dag(kubernetes_dag)


@repository
def with_airflow():
    return [airflow_complex_dag, airflow_simple_dag, airflow_kubernetes_dag]


# end_repo_marker_0

task_flow_dag_bag = DagBag(
    dag_folder=os.path.abspath("./with_airflow/task_flow_dags/"),
    include_examples=False,  # Exclude Airflow example dags
)
task_flow_schedules, task_flow_jobs = make_schedules_and_jobs_from_airflow_dag_bag(
    task_flow_dag_bag,
)


@repository
def task_flow_repo():
    return [*task_flow_schedules, *task_flow_jobs]


example_dag_bag = DagBag(
    dag_folder="some/empty/folder/with/no/dags",
    include_examples=True,  # Exclude Airflow example dags
)
example_schedules, example_jobs = make_schedules_and_jobs_from_airflow_dag_bag(
    example_dag_bag,
)


@repository
def airflow_examples_repo():
    return [*example_schedules, *example_jobs]


# start_repo_marker_1

airflow_simple_dag_with_execution_date = make_dagster_job_from_airflow_dag(
    dag=simple_dag, tags={"airflow_execution_date": datetime.now().isoformat()}
)
# end_repo_marker_1
