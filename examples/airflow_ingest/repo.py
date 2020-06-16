from airflow_complex_dag import complex_dag
from airflow_simple_dag import simple_dag
from dagster_airflow.dagster_pipeline_factory import make_dagster_pipeline_from_airflow_dag

from dagster import RepositoryDefinition

airflow_simple_dag = make_dagster_pipeline_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_pipeline_from_airflow_dag(complex_dag)


def define_repository():
    return RepositoryDefinition(
        "airflow_ingest", pipeline_defs=[airflow_complex_dag, airflow_simple_dag]
    )
