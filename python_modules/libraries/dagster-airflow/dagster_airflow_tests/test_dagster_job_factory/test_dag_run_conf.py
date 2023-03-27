import os
import tempfile

from airflow.models import DagBag, Variable
from dagster_airflow import (
    make_dagster_job_from_airflow_dag,
    make_ephemeral_airflow_db_resource,
)

from dagster_airflow_tests.marks import requires_local_db

DAG_RUN_CONF_DAG = """
from airflow import models

from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1)}

with models.DAG(
    dag_id="dag_run_conf_dag", default_args=default_args, schedule_interval='0 0 * * *',
) as dag_run_conf_dag:
    def test_function(**kwargs):
        Variable.set("CONFIGURATION_VALUE", kwargs['config_value'])

    PythonOperator(
        task_id="previous_macro_test",
        python_callable=test_function,
        provide_context=True,
        op_kwargs={'config_value': '{{dag_run.conf.get("configuration_key")}}'}
    )
"""


@requires_local_db
def test_dag_run_conf_local() -> None:
    with tempfile.TemporaryDirectory() as dags_path:
        with open(os.path.join(dags_path, "dag.py"), "wb") as f:
            f.write(bytes(DAG_RUN_CONF_DAG.encode("utf-8")))

        airflow_db = make_ephemeral_airflow_db_resource(dag_run_config={"configuration_key": "foo"})

        dag_bag = DagBag(dag_folder=dags_path)
        retry_dag = dag_bag.get_dag(dag_id="dag_run_conf_dag")

        job = make_dagster_job_from_airflow_dag(
            dag=retry_dag, resource_defs={"airflow_db": airflow_db}
        )

        result = job.execute_in_process()
        assert result.success
        assert Variable.get("CONFIGURATION_VALUE") == "foo"
