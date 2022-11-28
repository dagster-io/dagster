import os

# start_repo_marker_0
from dagster_airflow import (
    make_dagster_job_from_airflow_dag,
    make_dagster_repo_from_airflow_dags_path,
    make_dagster_repo_from_airflow_example_dags,
)
from with_airflow.airflow_complex_dag import complex_dag
from with_airflow.airflow_kubernetes_dag import kubernetes_dag
from with_airflow.airflow_simple_dag import simple_dag

from dagster import repository

airflow_simple_dag = make_dagster_job_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_job_from_airflow_dag(complex_dag)
airflow_kubernetes_dag = make_dagster_job_from_airflow_dag(kubernetes_dag, mock_xcom=True)


@repository
def with_airflow():
    return [airflow_complex_dag, airflow_simple_dag, airflow_kubernetes_dag]


# end_repo_marker_0


task_flow_repo = make_dagster_repo_from_airflow_dags_path(
    os.path.abspath("./with_airflow/task_flow_dags/"),
    "task_flow_repo",
)


airflow_examples_dags_repo = make_dagster_repo_from_airflow_example_dags()

# start_repo_marker_1

airflow_simple_dag_with_execution_date = make_dagster_job_from_airflow_dag(
    dag=simple_dag, tags={"airflow_execution_date": "2021-11-01 00:00:00+00:00"}
)
# end_repo_marker_1
