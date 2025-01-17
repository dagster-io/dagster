from collections.abc import Generator

import pytest
from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.utils import get_job_name
from dlift_kitchen_sink.instance import get_environment_id, get_project_id, get_unscoped_client


@pytest.fixture
def instance() -> UnscopedDbtCloudClient:
    return get_unscoped_client()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()


@pytest.fixture
def project_id() -> int:
    return get_project_id()


@pytest.fixture
def ensure_cleanup(
    instance: UnscopedDbtCloudClient, environment_id: int, project_id: int
) -> Generator[None, None, None]:
    try:
        yield
    finally:
        jobs = instance.list_jobs(environment_id)
        adhoc_job_ids = {
            job["id"] for job in jobs if job["name"] == get_job_name(project_id, environment_id)
        }
        for job_id in adhoc_job_ids:
            instance.destroy_dagster_job(job_id)
