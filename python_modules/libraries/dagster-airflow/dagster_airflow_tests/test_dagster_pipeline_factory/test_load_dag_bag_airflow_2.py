import os
import tempfile

import pytest
from airflow import __version__ as airflow_version
from dagster_airflow import (
    make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags,
)

from dagster_airflow_tests.airflow_utils import test_make_from_dagbag_inputs_airflow_2
from dagster_airflow_tests.marks import requires_local_db, requires_no_db


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@pytest.mark.parametrize(
    "path_and_content_tuples, fn_arg_path, expected_job_names",
    test_make_from_dagbag_inputs_airflow_2,
)
@requires_no_db
def test_make_repo(
    path_and_content_tuples,
    fn_arg_path,
    expected_job_names,
):
    with tempfile.TemporaryDirectory() as tmpdir_path:
        for path, content in path_and_content_tuples:
            with open(os.path.join(tmpdir_path, path), "wb") as f:
                f.write(bytes(content.encode("utf-8")))

        repo = (
            make_dagster_definitions_from_airflow_dags_path(
                tmpdir_path,
            )
            if fn_arg_path is None
            else make_dagster_definitions_from_airflow_dags_path(
                os.path.join(tmpdir_path, fn_arg_path)
            )
        ).get_repository_def()

        for job_name in expected_job_names:
            assert repo.has_job(job_name)

            job = repo.get_job(job_name)
            result = job.execute_in_process()
            assert result.success
            for event in result.all_events:
                assert event.event_type_value != "STEP_FAILURE"

        assert set(repo.job_names) == set(expected_job_names)


@pytest.fixture(scope="module")
def airflow_examples_repo():
    return make_dagster_definitions_from_airflow_example_dags().get_repository_def()


def get_examples_airflow_repo_params():
    repo = make_dagster_definitions_from_airflow_example_dags().get_repository_def()
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
        "example_subdag_operator",
        # runs slow
        "example_sensors",
        "example_dynamic_task_mapping",
        "example_dynamic_task_mapping_with_no_taskflow_operators",
        # wrong state
        "example_short_circuit_operator",
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
@requires_local_db
def test_airflow_example_dags(
    airflow_examples_repo,
    job_name,
    exclude_from_execution_tests,
):
    assert airflow_examples_repo.has_job(job_name)
    if not exclude_from_execution_tests:
        job = airflow_examples_repo.get_job(job_name)
        result = job.execute_in_process()
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"
