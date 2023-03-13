import datetime
import os
import tempfile
from typing import List

import pytest
import pytz
from _pytest.mark.structures import ParameterSet
from airflow import __version__ as airflow_version
from airflow.models import Pool, Variable
from dagster import (
    DagsterInstance,
    JobDefinition,
    ReexecutionOptions,
    RepositoryDefinition,
    build_reconstructable_job,
    execute_job,
)
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster_airflow import (
    make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags,
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
        value = Variable.get("RETRY_TEST", default_var="unset")
        if value == "set":
            print("variable exists")
        else:
            Variable.set("RETRY_TEST", "set")
            raise Exception("First run should fail with variable unset")

    PythonOperator(
        task_id="retry_test",
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


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_persistent_db
def test_retry_from_failure(instance: DagsterInstance, postgres_airflow_db: str):
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


POOL_DAG = """
from airflow import models

from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1)}

with models.DAG(
    dag_id="pool_dag", default_args=default_args, schedule_interval='0 0 * * *', tags=['example'],
) as pool_dag:
    def test_function(**kwargs):
        value = int(Variable.get("RUN_COUNTER", default_var="0"))
        Variable.set("RUN_COUNTER", str(value + 1))

    for i in range(10):
        PythonOperator(
            task_id="pool_test_" + str(i),
            python_callable=test_function,
            provide_context=True,
            pool="test_pool"
        )
"""


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_persistent_db
def test_pools(postgres_airflow_db: str):
    with tempfile.TemporaryDirectory() as dags_path:
        with open(os.path.join(dags_path, "dag.py"), "wb") as f:
            f.write(bytes(POOL_DAG.encode("utf-8")))

        Pool.create_or_update_pool(
            "test_pool",
            slots=1,
            description="Limit to 1 run",
        )

        airflow_db = make_persistent_airflow_db_resource(uri=postgres_airflow_db)

        definitions = make_dagster_definitions_from_airflow_dags_path(
            dags_path, resource_defs={"airflow_db": airflow_db}
        )
        job = definitions.get_job_def("pool_dag")
        result = job.execute_in_process()
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"
        # use an increment to make sure operators ran in succession, 1 at a time
        run_count = int(Variable.get("RUN_COUNTER", default_var="0"))
        assert run_count == 10


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


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_persistent_db
def test_prev_execution_date(postgres_airflow_db: str):
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


@pytest.fixture(scope="module")
def airflow_examples_repo(postgres_airflow_db) -> RepositoryDefinition:
    airflow_db = make_persistent_airflow_db_resource(uri=postgres_airflow_db)
    definitions = make_dagster_definitions_from_airflow_example_dags(
        resource_defs={"airflow_db": airflow_db}
    )
    return definitions.get_repository_def()


def get_examples_airflow_repo_params() -> List[ParameterSet]:
    definitions = make_dagster_definitions_from_airflow_example_dags()
    repo = definitions.get_repository_def()
    params = []
    no_job_run_dags = [
        # requires k8s environment to work
        # FileNotFoundError: [Errno 2] No such file or directory: '/foo/volume_mount_test.txt'
        "example_kubernetes_executor",
        # requires params to be passed in to work
        "example_passing_params_via_test_command",
        # requires template files to exist
        "example_python_operator",
        # requires email server to work
        "example_dag_decorator",
        # airflow.exceptions.DagNotFound: Dag id example_trigger_target_dag not found in DagModel
        "example_trigger_target_dag",
        "example_trigger_controller_dag",
        # runs slow
        "example_sensors",
    ]
    for job_name in repo.job_names:
        params.append(
            pytest.param(job_name, True if job_name in no_job_run_dags else False, id=job_name),
        )

    return params


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@pytest.mark.parametrize(
    "job_name, exclude_from_execution_tests",
    get_examples_airflow_repo_params(),
)
@requires_persistent_db
def test_airflow_example_dags_persistent_db(
    airflow_examples_repo: RepositoryDefinition,
    job_name: str,
    exclude_from_execution_tests: bool,
):
    assert airflow_examples_repo.has_job(job_name)
    if not exclude_from_execution_tests:
        job = airflow_examples_repo.get_job(job_name)
        result = job.execute_in_process()
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"
