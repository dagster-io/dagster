from dagster_airflow.utils import is_airflow_2_loaded_in_environment


# There is a bug in airflow v1
# 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2.
# v1.10 stable: https://github.com/apache/airflow/blob/v1-10-stable/airflow/example_dags/example_complex.py#L133
# master (05-05-2020): https://github.com/apache/airflow/blob/master/airflow/example_dags/example_complex.py#L136s
def patch_airflow_example_dag(dag_bag):
    if is_airflow_2_loaded_in_environment():
        return

    dag = dag_bag.dags.get("example_complex")
    task = dag.get_task("search_catalog")
    task.op_args = ["dummy"]

    return
