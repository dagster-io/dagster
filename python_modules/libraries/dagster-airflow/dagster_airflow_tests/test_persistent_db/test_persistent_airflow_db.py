import datetime
import os
import tempfile

import pytest
import pytz
from airflow import __version__ as airflow_version
from airflow.models import Variable
from dagster import (
    DagsterInstance,
    JobDefinition,
    ReexecutionOptions,
    build_reconstructable_job,
    execute_job,
)
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster_airflow import (
    make_dagster_definitions_from_airflow_dags_path,
    make_persistent_airflow_db_resource,
)

from dagster_airflow_tests.marks import requires_persistent_db

RETRY_DAG = """
from airflow import models

from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1)}

with models.DAG(
    dag_id="retry_dag", default_args=default_args, schedule_interval='0 0 * * *', tags=['example'],
) as retry_dag:
    def test_function(**kwargs):
        print("test_function EXECUTED")
        value = Variable.get("RETRY_TEST_AIRFLOW_1", default_var="unset")
        if value == "set":
            print("variable exists")
        else:
            Variable.set("RETRY_TEST_AIRFLOW_1", "set")
            raise Exception("First run should fail with variable unset")

    PythonOperator(
        task_id="retry_test",
        retries=0,
        python_callable=test_function,
        provide_context=True,
    )
"""


def reconstruct_retry_job(postgres_airflow_db: str, dags_path: str, *_args) -> JobDefinition:
    airflow_db = make_persistent_airflow_db_resource(uri=postgres_airflow_db)

    definitions = make_dagster_definitions_from_airflow_dags_path(
        dags_path, resource_defs={"airflow_db": airflow_db}
    )
    job = definitions.get_job_def("retry_dag")
    return job


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@requires_persistent_db
def test_retry_from_failure(instance: DagsterInstance, postgres_airflow_db: str) -> None:
    with tempfile.TemporaryDirectory() as dags_path:
        with open(os.path.join(dags_path, "dag.py"), "wb") as f:
            f.write(bytes(RETRY_DAG.encode("utf-8")))
        utc_date_string = "2023-02-01T00:00:00+00:00"

        reconstructable_job = build_reconstructable_job(
            reconstructor_module_name="test_persistent_airflow_db",
            reconstructor_function_name="reconstruct_retry_job",
            reconstructor_working_directory=os.path.dirname(os.path.realpath(__file__)),
            reconstructable_kwargs={
                "postgres_airflow_db": postgres_airflow_db,
                "dags_path": dags_path,
            },
        )

        # Initial execution
        initial_result = execute_job(
            job=reconstructable_job,
            instance=instance,
            tags={"airflow_execution_date": utc_date_string},
        )
        assert not initial_result.success

        options = ReexecutionOptions.from_failure(initial_result.run_id, instance)
        from_failure_result = execute_job(
            job=reconstructable_job,
            instance=instance,
            reexecution_options=options,
            tags={"airflow_execution_date": utc_date_string},
        )
        assert from_failure_result.success


PREVIOUS_MACRO_DAG = """
from airflow import models

from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1)}

with models.DAG(
    dag_id="previous_macro_dag", default_args=default_args, schedule_interval='0 0 * * *',
) as previous_macro_dag:
    def test_function(**kwargs):
        Variable.set("PREVIOUS_EXECUTION", kwargs['prev_execution'])

    PythonOperator(
        task_id="previous_macro_test",
        python_callable=test_function,
        provide_context=True,
        op_kwargs={'prev_execution': "{{ prev_execution_date }}"}
    )
"""


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@requires_persistent_db
def test_prev_execution_date(postgres_airflow_db: str) -> None:
    with tempfile.TemporaryDirectory() as dags_path:
        with open(os.path.join(dags_path, "dag.py"), "wb") as f:
            f.write(bytes(PREVIOUS_MACRO_DAG.encode("utf-8")))

        airflow_db = make_persistent_airflow_db_resource(uri=postgres_airflow_db)

        definitions = make_dagster_definitions_from_airflow_dags_path(
            dags_path, resource_defs={"airflow_db": airflow_db}
        )
        job = definitions.get_job_def("previous_macro_dag")

        result = job.execute_in_process(
            tags={AIRFLOW_EXECUTION_DATE_STR: datetime.datetime(2023, 2, 2).isoformat()}
        )
        assert result.success
        assert (
            Variable.get("PREVIOUS_EXECUTION")
            == datetime.datetime(2023, 2, 1, tzinfo=pytz.UTC).isoformat()
        )
