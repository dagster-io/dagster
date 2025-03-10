import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest
import responses
from dagster_dbt.cloud.resources import (
    DbtCloudCredentials,
    DbtCloudWorkspace,
    get_dagster_adhoc_job_name,
)
from dagster_dbt.cloud.types import DbtCloudJobRunStatusType

tests_path = Path(__file__).joinpath("..").resolve()
manifest_path = tests_path.joinpath("manifest.json")
run_results_path = tests_path.joinpath("run_results.json")


TEST_ACCOUNT_ID = 1111
TEST_ACCESS_URL = "https://cloud.getdbt.com"
TEST_TOKEN = "test_token"

TEST_PROJECT_ID = 2222
TEST_ENVIRONMENT_ID = 3333

TEST_JOB_ID = 4444
TEST_RUN_ID = 5555
TEST_ADHOC_JOB_NAME = get_dagster_adhoc_job_name(
    project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID
)
TEST_ANOTHER_JOB_NAME = "test_another_job_name"

TEST_REST_API_BASE_URL = f"{TEST_ACCESS_URL}/api/v2/accounts/{TEST_ACCOUNT_ID}"


def get_sample_manifest_json() -> Mapping[str, Any]:
    with open(manifest_path) as f:
        sample_manifest_json = json.load(f)
    return sample_manifest_json


def get_sample_run_results_json() -> Mapping[str, Any]:
    with open(run_results_path) as f:
        sample_run_results_json = json.load(f)
    return sample_run_results_json


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
            "account_id": TEST_ACCOUNT_ID,
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
            "account_id": TEST_ACCOUNT_ID,
            "project_id": TEST_PROJECT_ID,
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


# Taken from dbt Cloud REST API documentation
# https://docs.getdbt.com/dbt-cloud/api-v2#/operations/Retrieve%20Run
def get_sample_run_response(run_status: int) -> Mapping[str, Any]:
    return {
        "data": {
            "id": TEST_RUN_ID,
            "trigger_id": 0,
            "account_id": TEST_ACCOUNT_ID,
            "environment_id": TEST_ENVIRONMENT_ID,
            "project_id": TEST_PROJECT_ID,
            "job_definition_id": TEST_JOB_ID,
            "status": run_status,
            "dbt_version": "string",
            "git_branch": "string",
            "git_sha": "string",
            "status_message": "string",
            "owner_thread_id": "string",
            "executed_by_thread_id": "string",
            "deferring_run_id": 0,
            "artifacts_saved": True,
            "artifact_s3_path": "string",
            "has_docs_generated": True,
            "has_sources_generated": True,
            "notifications_sent": True,
            "blocked_by": [0],
            "created_at": "2019-08-24T14:15:22Z",
            "updated_at": "2019-08-24T14:15:22Z",
            "dequeued_at": "2019-08-24T14:15:22Z",
            "started_at": "2019-08-24T14:15:22Z",
            "finished_at": "2019-08-24T14:15:22Z",
            "last_checked_at": "2019-08-24T14:15:22Z",
            "last_heartbeat_at": "2019-08-24T14:15:22Z",
            "should_start_at": "2019-08-24T14:15:22Z",
            "trigger": {
                "cause": "string",
                "job_definition_id": TEST_JOB_ID,
                "git_branch": "string",
                "git_sha": "string",
                "azure_pull_request_id": 0,
                "github_pull_request_id": 0,
                "gitlab_merge_request_id": 0,
                "non_native_pull_request_id": 0,
                "schema_override": "string",
                "dbt_version_override": "string",
                "threads_override": 0,
                "target_name_override": "string",
                "generate_docs_override": True,
                "timeout_seconds_override": 0,
                "steps_override": ["string"],
                "cause_category": "api",
            },
            "job": {
                "account_id": TEST_ACCOUNT_ID,
                "project_id": TEST_PROJECT_ID,
                "environment_id": TEST_ENVIRONMENT_ID,
                "name": "string",
                "dbt_version": "string",
                "deferring_environment_id": 0,
                "deferring_job_definition_id": 0,
                "description": "",
                "execute_steps": ["string"],
                "execution": {"timeout_seconds": 0},
                "generate_docs": True,
                "job_type": "ci",
                "lifecycle_webhooks": True,
                "run_compare_changes": True,
                "compare_changes_flags": "--select state:modified",
                "run_generate_sources": True,
                "run_lint": True,
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
                "schedule": {"cron": "string", "date": "every_day", "time": "every_hour"},
            },
            "environment": {
                "account_id": TEST_ACCOUNT_ID,
                "project_id": TEST_PROJECT_ID,
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
            "run_steps": [
                {
                    "run_id": TEST_RUN_ID,
                    "account_id": TEST_ACCOUNT_ID,
                    "index": 0,
                    "status": run_status,
                    "name": "string",
                    "logs": "string",
                    "debug_logs": "string",
                    "log_path": "string",
                    "debug_log_path": "string",
                }
            ],
            "status_humanized": "string",
            "in_progress": True,
            "is_complete": True,
            "is_success": True,
            "is_error": True,
            "is_cancelled": True,
            "duration": "string",
            "queued_duration": "string",
            "run_duration": "string",
            "duration_humanized": "string",
            "queued_duration_humanized": "string",
            "run_duration_humanized": "string",
            "created_at_humanized": "string",
            "finished_at_humanized": "string",
            "retrying_run_id": 0,
            "can_retry": True,
            "retry_not_supported_reason": "RETRY_UNSUPPORTED_CMD",
            "job_id": 0,
            "is_running": True,
            "href": "string",
            "used_repo_cache": True,
        },
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "string",
            "developer_message": "string",
        },
    }


SAMPLE_SUCCESS_RUN_RESPONSE = get_sample_run_response(
    run_status=int(DbtCloudJobRunStatusType.SUCCESS)
)


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
    name="job_api_mocks",
)
def job_api_mocks_fixture() -> Iterator[responses.RequestsMock]:
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


@pytest.fixture(
    name="fetch_workspace_data_api_mocks",
)
def fetch_workspace_data_api_mocks_fixture(
    job_api_mocks: responses.RequestsMock,
) -> Iterator[responses.RequestsMock]:
    job_api_mocks.add(
        method=responses.GET,
        url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
        json=SAMPLE_SUCCESS_RUN_RESPONSE,
        status=200,
    )
    job_api_mocks.add(
        method=responses.POST,
        url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_JOB_ID}/run",
        json=SAMPLE_SUCCESS_RUN_RESPONSE,
        status=201,
    )
    job_api_mocks.add(
        method=responses.GET,
        url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}/artifacts/manifest.json",
        json=get_sample_manifest_json(),
        status=200,
    )
    yield job_api_mocks


@pytest.fixture(
    name="all_api_mocks",
)
def all_api_mocks_fixture(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> Iterator[responses.RequestsMock]:
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}/artifacts/run_results.json",
        json=get_sample_run_results_json(),
        status=200,
    )
    yield fetch_workspace_data_api_mocks
