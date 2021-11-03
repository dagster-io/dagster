from dagster_airflow.operators.docker_operator import DagsterDockerOperator
from dagster_airflow.operators.python_operator import DagsterPythonOperator
from docs_snippets.integrations.airflow.hello_cereal import hello_cereal_job


def test_hello_cereal():
    assert hello_cereal_job.execute_in_process().success


def test_hello_cereal_dag():
    from docs_snippets.integrations.airflow.hello_cereal_dag import dag, tasks

    assert dag.dag_id == "hello_cereal_job"

    for task in tasks:
        assert isinstance(task, DagsterPythonOperator)


def test_containerized():
    from docs_snippets.integrations.airflow.containerized import dag, steps

    assert dag.dag_id == "hello_cereal_job"

    for step in steps:
        assert isinstance(step, DagsterDockerOperator)
