from airflow_ingest.airflow_complex_dag import complex_dag
from airflow_ingest.airflow_simple_dag import simple_dag
from dagster_airflow.dagster_pipeline_factory import make_dagster_pipeline_from_airflow_dag

from dagster import repository

airflow_simple_dag = make_dagster_pipeline_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_pipeline_from_airflow_dag(complex_dag)


@repository
def airflow_ingest_example():
    return [airflow_complex_dag, airflow_simple_dag]
