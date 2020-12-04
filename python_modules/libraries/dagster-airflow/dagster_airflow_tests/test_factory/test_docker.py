# pylint: disable=unused-import
import os
import sys
import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.utils import make_new_run_id
from dagster.utils import git_repository_root, load_yaml_from_glob_list
from dagster_airflow.factory import make_airflow_dag_containerized_for_recon_repo
from dagster_airflow_tests.conftest import dagster_docker_image
from dagster_airflow_tests.marks import nettest, requires_airflow_db
from dagster_airflow_tests.test_fixtures import (
    dagster_airflow_docker_operator_pipeline,
    execute_tasks_in_dag,
    postgres_instance,
)
from dagster_test.test_project import get_test_project_environments_path

from .utils import validate_pipeline_execution, validate_skip_pipeline_execution


@requires_airflow_db
def test_fs_storage_no_explicit_base_dir(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = "demo_pipeline"
    environments_path = get_test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_filesystem_no_explicit_base_dir.yaml"),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@requires_airflow_db
def test_fs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = "demo_pipeline"
    environments_path = get_test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_filesystem.yaml"),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
@requires_airflow_db
def test_s3_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = "demo_pipeline"
    environments_path = get_test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_s3.yaml"),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
@requires_airflow_db
def test_gcs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image,
):  # pylint: disable=redefined-outer-name
    pipeline_name = "demo_pipeline_gcs"
    environments_path = get_test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[
            os.path.join(environments_path, "env.yaml"),
            os.path.join(environments_path, "env_gcs.yaml"),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@requires_airflow_db
def test_skip_operator(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image
):  # pylint: disable=redefined-outer-name
    pipeline_name = "optional_outputs"
    environments_path = get_test_project_environments_path()
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        recon_repo=ReconstructableRepository.for_module(
            "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo",
        ),
        environment_yaml=[os.path.join(environments_path, "env_filesystem.yaml")],
        op_kwargs={"host_tmp_dir": "/tmp"},
        image=dagster_docker_image,
    )
    validate_skip_pipeline_execution(results)


@requires_airflow_db
def test_error_dag_containerized(dagster_docker_image):  # pylint: disable=redefined-outer-name
    pipeline_name = "demo_error_pipeline"
    recon_repo = ReconstructableRepository.for_module(
        "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo"
    )
    environments_path = get_test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, "env_s3.yaml"),
    ]
    run_config = load_yaml_from_glob_list(environment_yaml)

    run_id = make_new_run_id()
    execution_date = timezone.utcnow()

    with postgres_instance() as instance:

        dag, tasks = make_airflow_dag_containerized_for_recon_repo(
            recon_repo,
            pipeline_name,
            dagster_docker_image,
            run_config,
            instance=instance,
            op_kwargs={"network_mode": "container:test-postgres-db-airflow"},
        )

        with pytest.raises(AirflowException) as exc_info:
            execute_tasks_in_dag(dag, tasks, run_id, execution_date)

        assert "Exception: Unusual error" in str(exc_info.value)


@requires_airflow_db
def test_airflow_execution_date_tags_containerized(
    dagster_docker_image,
):  # pylint: disable=redefined-outer-name, unused-argument
    pipeline_name = "demo_airflow_execution_date_pipeline"
    recon_repo = ReconstructableRepository.for_module(
        "dagster_test.test_project.test_pipelines.repo", "define_demo_execution_repo"
    )
    environments_path = get_test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, "env_s3.yaml"),
    ]
    run_config = load_yaml_from_glob_list(environment_yaml)

    execution_date = timezone.utcnow()

    with postgres_instance() as instance:
        dag, tasks = make_airflow_dag_containerized_for_recon_repo(
            recon_repo,
            pipeline_name,
            dagster_docker_image,
            run_config,
            instance=instance,
            op_kwargs={"network_mode": "container:test-postgres-db-airflow"},
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
