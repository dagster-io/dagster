import responses
from dagster_dbt.cloud.resources import DbtCloudWorkspace

from dagster_dbt_tests.cloud.preview.conftest import (
    SAMPLE_MANIFEST_JSON,
    TEST_ENVIRONMENT_ID,
    TEST_JOB_ID,
    TEST_PROJECT_ID,
)


def test_fetch_dbt_cloud_workspace_data(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    workspace_data = workspace.fetch_workspace_data()
    assert workspace_data.project_id == TEST_PROJECT_ID
    assert workspace_data.environment_id == TEST_ENVIRONMENT_ID
    assert workspace_data.job_id == TEST_JOB_ID
    assert workspace_data.manifest == SAMPLE_MANIFEST_JSON
