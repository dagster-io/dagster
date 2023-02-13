from typing import List

import pytest
from _pytest.mark.structures import ParameterSet
from airflow import __version__ as airflow_version
from dagster import (
    RepositoryDefinition,
)
from dagster_airflow import (
    make_dagster_definitions_from_airflow_example_dags,
    make_persistent_airflow_db_resource,
)

from dagster_airflow_tests.marks import requires_persistent_db


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
