from collections.abc import Generator

import pytest
from dagster_dbt.cloud_v2.resources import DAGSTER_ADHOC_PREFIX, DbtCloudWorkspace
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
        # Resolve project / environment so the fixture validates the same IDs.
        DbtCloudProject.from_project_details(
            project_details=client.get_project_details(project_id=project_id)
        )
        DbtCloudEnvironment.from_environment_details(
            environment_details=client.get_environment_details(environment_id=environment_id)
        )
        # Clean up every Dagster-managed adhoc job (including suffixed pool entries).
        adhoc_job_ids = {
            job["id"] for job in jobs if (job.get("name") or "").startswith(DAGSTER_ADHOC_PREFIX)
        }
        for job_id in adhoc_job_ids:
            client.destroy_job(job_id=job_id)
