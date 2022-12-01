import pkg_resources


# There is a bug in airflow v1
# 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2.
# v1.10 stable: https://github.com/apache/airflow/blob/v1-10-stable/airflow/example_dags/example_complex.py#L133
# master (05-05-2020): https://github.com/apache/airflow/blob/master/airflow/example_dags/example_complex.py#L136s
def patch_airflow_example_dag(dag_bag):
    airflow_version = pkg_resources.get_distribution("apache-airflow").version
    if airflow_version >= "2.0.0":
        return

    dag = dag_bag.dags.get("example_complex")
    task = dag.get_task("search_catalog")
    task.op_args = ["dummy"]

    return
