from with_airflow.repository import (
    airflow_complex_dag,
    airflow_simple_dag,
    airflow_simple_dag_with_execution_date,
)


def test_airflow_simple_dag():
    assert airflow_simple_dag.execute_in_process()


def test_airflow_complex_dag():
    assert airflow_complex_dag.execute_in_process()


def test_airflow_simple_dag_with_execution_date():
    assert airflow_simple_dag_with_execution_date.execute_in_process()
