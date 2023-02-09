from with_airflow.definition import (
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


def test_node_outputs():
    dags = [airflow_complex_dag, airflow_simple_dag, airflow_simple_dag_with_execution_date]
    for dag in dags:
        result = dag.execute_in_process()
        for node in result.all_node_defs:
            assert result.output_for_node(node.name,output_name='airflow_task_complete') is None