from dagster_dlift.client import DbtCloudClient
from dagster_dlift.translator import (
    DbtCloudContentData,
    DbtCloudContentType,
    DbtCloudProjectEnvironmentData,
)


def compute_environment_data(
    environment_id: int, project_id: int, client: DbtCloudClient
) -> DbtCloudProjectEnvironmentData:
    """Compute the data for a dbt Cloud project environment."""
    return DbtCloudProjectEnvironmentData(
        project_id=project_id,
        environment_id=environment_id,
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
