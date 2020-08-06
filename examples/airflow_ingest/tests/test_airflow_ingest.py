from airflow_ingest.repo import airflow_complex_dag, airflow_simple_dag

from dagster import execute_pipeline


def test_airflow_simple_dag():
    result = execute_pipeline(airflow_simple_dag)
    assert result.success


def test_airflow_complex_dag():
    result = execute_pipeline(airflow_complex_dag)
    assert result.success
