from dagster._annotations import preview

from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.translator import (
    DbtCloudContentData,
    DbtCloudContentType,
    DbtCloudProjectEnvironmentData,
)
from dagster_dlift.utils import get_job_name


@preview
def compute_environment_data(
    environment_id: int, project_id: int, client: UnscopedDbtCloudClient
) -> DbtCloudProjectEnvironmentData:
    """Compute the data for a dbt Cloud project environment."""
    return DbtCloudProjectEnvironmentData(
        project_id=project_id,
        environment_id=environment_id,
        job_id=get_or_create_job(environment_id, project_id, client),
        models_by_unique_id={
            model["uniqueId"]: DbtCloudContentData(
                content_type=DbtCloudContentType.MODEL,
                properties=model,
            )
            for model in client.get_dbt_models(environment_id)
        },
        sources_by_unique_id={
            source["uniqueId"]: DbtCloudContentData(
                content_type=DbtCloudContentType.SOURCE,
                properties=source,
            )
            for source in client.get_dbt_sources(environment_id)
        },
        tests_by_unique_id={
            test["uniqueId"]: DbtCloudContentData(
                content_type=DbtCloudContentType.TEST,
                properties=test,
            )
            for test in client.get_dbt_tests(environment_id)
        },
    )


@preview
def get_or_create_job(environment_id: int, project_id: int, client: UnscopedDbtCloudClient) -> int:
    """Get or create a dbt Cloud job for a project environment."""
    expected_job_name = get_job_name(project_id, environment_id)
    if expected_job_name in {
        job["name"] for job in client.list_jobs(environment_id=environment_id)
    }:
        return next(
            job["id"]
            for job in client.list_jobs(environment_id=environment_id)
            if job["name"] == expected_job_name
        )
    return client.create_job(
        project_id=project_id, environment_id=environment_id, job_name=expected_job_name
    )
