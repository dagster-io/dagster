from collections.abc import Iterator, Mapping
from typing import Any

import pytest
import responses
from dagster_dbt.cloud.resources import (
    DbtCloudCredentials,
    DbtCloudWorkspace,
    get_dagster_adhoc_job_name,
)

TEST_ACCOUNT_ID = 1111
TEST_ACCESS_URL = "https://cloud.getdbt.com"
TEST_TOKEN = "test_token"

TEST_PROJECT_ID = 2222
TEST_ENVIRONMENT_ID = 3333

TEST_JOB_ID = "test_job_id"
TEST_ADHOC_JOB_NAME = get_dagster_adhoc_job_name(
    project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID
)
TEST_ANOTHER_JOB_NAME = "test_another_job_name"

TEST_REST_API_BASE_URL = f"{TEST_ACCESS_URL}/api/v2/accounts/{TEST_ACCOUNT_ID}"


# Taken from dbt Cloud REST API documentation
# https://docs.getdbt.com/dbt-cloud/api-v2#/operations/Create%20Job
def get_sample_job_data(job_name: str) -> Mapping[str, Any]:
    return {
        "id": TEST_JOB_ID,
        "account_id": TEST_ACCOUNT_ID,
        "project_id": TEST_PROJECT_ID,
        "environment_id": TEST_ENVIRONMENT_ID,
        "name": job_name,
        "dbt_version": "string",
        "deferring_environment_id": 0,
        "deferring_job_definition_id": 0,
        "description": "",
        "execute_steps": ["string"],
        "execution": {"timeout_seconds": 0},
        "generate_docs": False,
        "is_deferrable": False,
        "job_type": "ci",
        "lifecycle_webhooks_url": "string",
        "lifecycle_webhooks": False,
        "raw_dbt_version": "string",
        "run_compare_changes": False,
        "compare_changes_flags": "--select state:modified",
        "run_failure_count": 0,
        "run_generate_sources": False,
        "run_lint": False,
        "errors_on_lint_failure": True,
        "settings": {"threads": 0, "target_name": "string"},
        "state": 1,
        "triggers_on_draft_pr": False,
        "triggers": {
            "github_webhook": True,
            "schedule": True,
            "git_provider_webhook": True,
            "on_merge": True,
            "custom_branch_only": True,
        },
        "job_completion_trigger_condition": None,
        "created_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z",
        "account": {"name": "string", "state": 1, "docs_job_id": 0, "freshness_job_id": 0},
        "project": {
            "name": "string",
            "account_id": 0,
            "description": "string",
            "connection_id": 0,
            "repository_id": 0,
            "semantic_layer_config_id": 0,
            "state": 1,
            "dbt_project_subdirectory": "string",
            "docs_job_id": 0,
            "freshness_job_id": 0,
        },
        "environment": {
            "account_id": 0,
            "project_id": 0,
            "name": "string",
            "connection_id": 0,
            "credentials_id": 0,
            "repository_id": 0,
            "extended_attributes_id": 0,
            "custom_branch": "string",
            "use_custom_branch": True,
            "dbt_project_subdirectory": "string",
            "dbt_version": "string",
            "supports_docs": True,
            "deployment_type": "production",
            "type": "development",
            "created_by_id": 0,
            "state": 1,
        },
        "schedule": {
            "date": {"type": "every_day", "days": [0], "cron": "string"},
            "time": {"type": "every_hour", "hours": [0], "interval": 1},
            "cron": "string",
        },
        "generate_sources": False,
    }


SAMPLE_CREATE_JOB_RESPONSE = {
    "data": get_sample_job_data(job_name=TEST_ADHOC_JOB_NAME),
    "status": {
        "code": 201,
        "is_success": True,
        "user_message": "string",
        "developer_message": "string",
    },
}

# Taken from dbt Cloud REST API documentation
# https://docs.getdbt.com/dbt-cloud/api-v2#/operations/List%20Jobs
SAMPLE_LIST_JOBS_RESPONSE = {
    "data": [get_sample_job_data(job_name=TEST_ANOTHER_JOB_NAME)],
    "extra": {
        "filters": {"property1": None, "property2": None},
        "order_by": "string",
        "pagination": {"count": 0, "total_count": 0},
    },
    "status": {
        "code": 200,
        "is_success": True,
        "user_message": "string",
        "developer_message": "string",
    },
}


@pytest.fixture(name="credentials")
def credentials_fixture() -> DbtCloudCredentials:
    return DbtCloudCredentials(
        account_id=TEST_ACCOUNT_ID,
        access_url=TEST_ACCESS_URL,
        token=TEST_TOKEN,
    )


@pytest.fixture(name="workspace")
def workspace_fixture(credentials: DbtCloudCredentials) -> DbtCloudWorkspace:
    return DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
    )


@pytest.fixture(
    name="api_mocks",
)
def api_mocks_fixture() -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as response:
        response.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/jobs",
            json=SAMPLE_LIST_JOBS_RESPONSE,
            status=200,
        )
        response.add(
            method=responses.POST,
            url=f"{TEST_REST_API_BASE_URL}/jobs",
            json=SAMPLE_CREATE_JOB_RESPONSE,
            status=201,
        )
        yield response
