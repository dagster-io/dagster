import os
import tempfile

import pytest
from airflow import __version__ as airflow_version
from airflow.models import DagBag
from dagster_airflow import (
    make_dagster_definitions_from_airflow_dags_path,
    make_dagster_definitions_from_airflow_example_dags,
    make_dagster_job_from_airflow_dag,
)

from dagster_airflow_tests.marks import requires_local_db

from ..airflow_utils import test_make_from_dagbag_inputs


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@pytest.mark.parametrize(
    "path_and_content_tuples, fn_arg_path, expected_job_names",
    test_make_from_dagbag_inputs,
)
def test_make_definitions(
    path_and_content_tuples,
    fn_arg_path,
    expected_job_names,
):
    with tempfile.TemporaryDirectory() as tmpdir_path:
        for path, content in path_and_content_tuples:
            with open(os.path.join(tmpdir_path, path), "wb") as f:
                f.write(bytes(content.encode("utf-8")))

        definitions = (
            make_dagster_definitions_from_airflow_dags_path(tmpdir_path)
            if fn_arg_path is None
            else make_dagster_definitions_from_airflow_dags_path(
                os.path.join(tmpdir_path, fn_arg_path)
            )
        )
        repo = definitions.get_repository_def()

        for job_name in expected_job_names:
            assert repo.has_job(job_name)

            job = definitions.get_job_def(job_name)
            result = job.execute_in_process()
            assert result.success
            for event in result.all_events:
                assert event.event_type_value != "STEP_FAILURE"

        assert set(repo.job_names) == set(expected_job_names)


test_airflow_example_dags_inputs = [
    (
        [
            "example_bash_operator",
            "example_branch_dop_operator_v3",
            "example_branch_operator",
            "example_complex",
            "example_external_task_marker_child",
            "example_external_task_marker_parent",
            "example_http_operator",
            "example_kubernetes_executor_config",
            "example_nested_branch_dag",  # only exists in airflow v1.10.10
            "example_passing_params_via_test_command",
            "example_pig_operator",
            "example_python_operator",
            "example_short_circuit_operator",
            "example_skip_dag",
            "example_subdag_operator",
            "example_subdag_operator_section_1",
            "example_subdag_operator_section_2",
            "example_trigger_controller_dag",
            "example_trigger_target_dag",
            "example_xcom",
            "latest_only",
            "latest_only_with_trigger",
            "test_utils",
            "tutorial",
        ],
        [
            #  No such file or directory: '/foo/volume_mount_test.txt'
            "example_kubernetes_executor_config",
            # [Errno 2] No such file or directory: 'pig'
            "example_pig_operator",
            # airflow.exceptions.DagNotFound: Dag id example_trigger_target_dag not found in DagModel
            "example_trigger_controller_dag",
            # 'NoneType' object is not subscriptable, target dag does not exist
            "example_trigger_target_dag",
            # sleeps forever, not an example
            "test_utils",
            # patching airflow.models.DAG causes this to fail
            "example_complex",
            # can flake due to 502 Server Error: Bad Gateway for url: https://www.httpbin.org/
            "example_http_operator",
        ],
    ),
]


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@pytest.mark.parametrize(
    "expected_job_names, exclude_from_execution_tests",
    test_airflow_example_dags_inputs,
)
@requires_local_db
def test_airflow_example_dags(
    expected_job_names,
    exclude_from_execution_tests,
):
    definitions = make_dagster_definitions_from_airflow_example_dags()
    repo = definitions.get_repository_def()

    for job_name in expected_job_names:
        assert repo.has_job(job_name)

        if job_name not in exclude_from_execution_tests:
            job = repo.get_job(job_name)
            result = job.execute_in_process()
            assert result.success
            for event in result.all_events:
                assert event.event_type_value != "STEP_FAILURE"

    assert set(repo.job_names) == set(expected_job_names)


RETRY_DAG = """
from airflow import models

from airflow.operators.bash_operator import BashOperator
import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1), "retries": 3}

with models.DAG(
    dag_id="retry_dag", default_args=default_args, schedule_interval='0 0 * * *', tags=['example'],
) as retry_dag:
    foo = BashOperator(
        task_id="foo", bash_command="echo foo", retries=1
    )

    bar = BashOperator(
        task_id="bar", bash_command="echo bar"
    )
"""


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@requires_local_db
def test_retry_conversion():
    with tempfile.TemporaryDirectory(suffix="retries") as tmpdir_path:
        with open(os.path.join(tmpdir_path, "dag.py"), "wb") as f:
            f.write(bytes(RETRY_DAG.encode("utf-8")))

        dag_bag = DagBag(dag_folder=tmpdir_path)
        retry_dag = dag_bag.get_dag(dag_id="retry_dag")

        job = make_dagster_job_from_airflow_dag(dag=retry_dag)
        result = job.execute_in_process()
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"
