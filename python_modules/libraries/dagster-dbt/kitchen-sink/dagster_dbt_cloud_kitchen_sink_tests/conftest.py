from collections.abc import Generator

import pytest
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace, get_dagster_adhoc_job_name
from dagster_dbt.cloud_v2.types import DbtCloudEnvironment, DbtCloudProject
from dagster_dbt_cloud_kitchen_sink.resources import (
    get_dbt_cloud_workspace,
    get_environment_id,
    get_project_id,
)


@pytest.fixture
def workspace() -> DbtCloudWorkspace:
    return get_dbt_cloud_workspace()


@pytest.fixture
def project_id() -> int:
    return get_project_id()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()


@pytest.fixture
def ensure_cleanup(
    workspace: DbtCloudWorkspace,
    project_id: int,
    environment_id: int,
) -> Generator[None, None, None]:
    """Cleans up jobs created by Dagster after the tests are completed."""
    try:
        yield
    finally:
        client = workspace.get_client()
        jobs = client.list_jobs(project_id=project_id, environment_id=environment_id)
        project = DbtCloudProject.from_project_details(
            project_details=client.get_project_details(project_id=project_id)
        )
        environment = DbtCloudEnvironment.from_environment_details(
            environment_details=client.get_environment_details(environment_id=environment_id)
        )
        adhoc_job_ids = {
            job["id"]
            for job in jobs
            if job["name"]
            == get_dagster_adhoc_job_name(
                project_id=project.id,
                project_name=project.name,
                environment_id=environment.id,
                environment_name=environment.name,
            )
        }
        for job_id in adhoc_job_ids:
            client.destroy_job(job_id=job_id)
