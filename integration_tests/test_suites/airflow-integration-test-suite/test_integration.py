# pylint: disable=redefined-outer-name, unused-argument

import os

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import make_airflow_dag_kubernetized_for_recon_repo
from dagster_airflow_tests.marks import nettest
from dagster_airflow_tests.test_factory.utils import validate_pipeline_execution
from dagster_airflow_tests.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_k8s_operator_pipeline,
    execute_tasks_in_dag,
)
from dagster_test.test_project import test_project_environments_path

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.utils import make_new_run_id
from dagster.utils import load_yaml_from_glob_list


@nettest
def test_s3_storage(dagster_airflow_k8s_operator_pipeline, dagster_docker_image, cluster_provider):
    _check_aws_creds_available()
    environments_path = test_project_environments_path()

    pipeline_name = "demo_pipeline"
    results = dagster_airflow_k8s_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_s3.yaml"),
        ],
        image=dagster_docker_image,
        op_kwargs={
            "config_file": os.environ["KUBECONFIG"],
            "env_vars": {
                "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
                "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
            },
        },
    )
    validate_pipeline_execution(results)


@nettest
def test_gcs_storage(
    dagster_airflow_k8s_operator_pipeline, dagster_docker_image, cluster_provider,
):
    environments_path = test_project_environments_path()

    pipeline_name = "demo_pipeline_gcs"
    results = dagster_airflow_k8s_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_gcs.yaml"),
        ],
        image=dagster_docker_image,
        op_kwargs={"config_file": os.environ["KUBECONFIG"]},
    )
    validate_pipeline_execution(results)


def test_error_dag_k8s(dagster_docker_image, cluster_provider):
    _check_aws_creds_available()

    pipeline_name = "demo_error_pipeline"
    recon_repo = ReconstructableRepository.for_module(
        "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo"
    )
    environments_path = test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, "env_s3.yaml"),
    ]
    run_config = load_yaml_from_glob_list(environment_yaml)

    run_id = make_new_run_id()
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_kubernetized_for_recon_repo(
        recon_repo=recon_repo,
        pipeline_name=pipeline_name,
        image=dagster_docker_image,
        namespace="default",
        run_config=run_config,
        op_kwargs={
            "config_file": os.environ["KUBECONFIG"],
            "env_vars": {
                "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
                "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
            },
        },
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert "Exception: Unusual error" in str(exc_info.value)


def test_airflow_execution_date_tags_k8s(dagster_docker_image, cluster_provider):
    _check_aws_creds_available()

    pipeline_name = "demo_airflow_execution_date_pipeline"
    recon_repo = ReconstructableRepository.for_module(
        "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo"
    )
    environments_path = test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, "env_s3.yaml"),
    ]
    run_config = load_yaml_from_glob_list(environment_yaml)

    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_kubernetized_for_recon_repo(
        recon_repo=recon_repo,
        pipeline_name=pipeline_name,
        image=dagster_docker_image,
        namespace="default",
        run_config=run_config,
        op_kwargs={
            "config_file": os.environ["KUBECONFIG"],
            "env_vars": {
                "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
                "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
            },
        },
    )

    results = execute_tasks_in_dag(
        dag, tasks, run_id=make_new_run_id(), execution_date=execution_date
    )

    materialized_airflow_execution_date = None
    for result in results.values():
        for event in result:
            if event.event_type_value == "STEP_MATERIALIZATION":
                materialization = event.event_specific_data.materialization
                materialization_entry = materialization.metadata_entries[0]
                materialized_airflow_execution_date = materialization_entry.entry_data.text

    assert execution_date.isoformat() == materialized_airflow_execution_date


def _check_aws_creds_available():
    for expected_env_var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
        if expected_env_var not in os.environ:
            raise Exception(
                "Could not find %s in environment; AWS credentials AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY must be set in environment for dagster-airflow k8s tests to "
                "run, as credentials are needed to access S3 from within the Docker container "
                "running on kind." % expected_env_var
            )
