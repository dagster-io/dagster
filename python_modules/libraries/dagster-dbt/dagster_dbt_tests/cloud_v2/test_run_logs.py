import sys
from io import StringIO
from unittest.mock import patch

import responses
from dagster_dbt.cloud_v2.cli_invocation import DbtCloudCliInvocation
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_ACCESS_URL,
    TEST_ACCOUNT_ID,
    TEST_ADHOC_JOB_ID,
    TEST_REST_API_BASE_URL,
    TEST_RUN_ID,
    TEST_TOKEN,
    get_sample_manifest_json,
    get_sample_run_response_with_logs,
    get_sample_run_results_json,
)


def test_get_run_logs_extracts_from_run_steps():
    """Test that get_run_logs correctly extracts and formats logs from run_steps."""
    client = DbtCloudWorkspaceClient(
        account_id=TEST_ACCOUNT_ID,
        token=TEST_TOKEN,
        access_url=TEST_ACCESS_URL,
        request_max_retries=3,
        request_retry_delay=0.25,
        request_timeout=30,
    )

    with responses.RequestsMock() as rsps:
        # Mock the get_run_details call with include_related=run_steps
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.SUCCESS)
            ),
            status=200,
            match=[responses.matchers.query_param_matcher({"include_related": "run_steps"})],
        )

        logs = client.get_run_logs(run_id=TEST_RUN_ID)

        # Verify logs are properly formatted with step headers
        assert "=== Step: Clone git repository ===" in logs
        assert "Cloning into '/tmp/jobs/12345/target'..." in logs
        assert "Successfully cloned repository." in logs

        assert "=== Step: Invoke dbt with `dbt build` ===" in logs
        assert "15:49:32  Running dbt..." in logs
        assert "15:49:34  Found 5 models, 13 data tests" in logs
        assert "15:49:35  Completed successfully" in logs


def test_get_run_logs_handles_empty_logs():
    """Test that get_run_logs handles run_steps with empty logs."""
    client = DbtCloudWorkspaceClient(
        account_id=TEST_ACCOUNT_ID,
        token=TEST_TOKEN,
        access_url=TEST_ACCESS_URL,
        request_max_retries=3,
        request_retry_delay=0.25,
        request_timeout=30,
    )

    with responses.RequestsMock() as rsps:
        # Mock response with empty run_steps
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json={
                "data": {
                    "id": TEST_RUN_ID,
                    "run_steps": [],
                },
                "status": {"code": 200, "is_success": True},
            },
            status=200,
            match=[responses.matchers.query_param_matcher({"include_related": "run_steps"})],
        )

        logs = client.get_run_logs(run_id=TEST_RUN_ID)

        # Should return empty string for no logs
        assert logs == ""


def test_run_handler_get_run_logs():
    """Test that DbtCloudJobRunHandler.get_run_logs works correctly."""
    client = DbtCloudWorkspaceClient(
        account_id=TEST_ACCOUNT_ID,
        token=TEST_TOKEN,
        access_url=TEST_ACCESS_URL,
        request_max_retries=3,
        request_retry_delay=0.25,
        request_timeout=30,
    )

    run_handler = DbtCloudJobRunHandler(
        job_id=TEST_ADHOC_JOB_ID,
        run_id=TEST_RUN_ID,
        args=["build"],
        client=client,
    )

    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.SUCCESS)
            ),
            status=200,
            match=[responses.matchers.query_param_matcher({"include_related": "run_steps"})],
        )

        logs = run_handler.get_run_logs()

        assert logs is not None
        assert "Clone git repository" in logs
        assert "Invoke dbt with `dbt build`" in logs


def test_cli_invocation_prints_logs_to_stdout():
    """Test that DbtCloudCliInvocation.wait() prints logs to stdout."""
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

    client = DbtCloudWorkspaceClient(
        account_id=TEST_ACCOUNT_ID,
        token=TEST_TOKEN,
        access_url=TEST_ACCESS_URL,
        request_max_retries=3,
        request_retry_delay=0.25,
        request_timeout=30,
    )

    with responses.RequestsMock() as rsps:
        # Mock job trigger
        rsps.add(
            method=responses.POST,
            url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_ADHOC_JOB_ID}/run",
            json={
                "data": {
                    "id": TEST_RUN_ID,
                    "trigger_id": 12345,
                    "account_id": TEST_ACCOUNT_ID,
                    "status": int(DbtCloudJobRunStatusType.QUEUED),
                },
                "status": {"code": 201, "is_success": True},
            },
            status=201,
        )

        # Mock poll_run - first call returns running, second returns success
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.RUNNING)
            ),
            status=200,
        )
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.SUCCESS)
            ),
            status=200,
        )

        # Mock get_run_details with run_steps for log retrieval
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.SUCCESS)
            ),
            status=200,
            match=[responses.matchers.query_param_matcher({"include_related": "run_steps"})],
        )

        # Mock get_run_details without include_related (for raise_for_status check)
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
            json=get_sample_run_response_with_logs(
                run_status=int(DbtCloudJobRunStatusType.SUCCESS)
            ),
            status=200,
        )

        # Mock list_run_artifacts
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}/artifacts",
            json={"data": ["manifest.json", "run_results.json"]},
            status=200,
        )

        # Mock get_run_artifact for run_results.json
        rsps.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}/artifacts/run_results.json",
            json=get_sample_run_results_json(),
            status=200,
        )

        invocation = DbtCloudCliInvocation.run(
            job_id=TEST_ADHOC_JOB_ID,
            args=["build"],
            client=client,
            manifest=get_sample_manifest_json(),
            dagster_dbt_translator=DagsterDbtTranslator(),
            context=None,
        )

        # Capture stdout
        captured_output = StringIO()
        with patch.object(sys, "stdout", captured_output):
            # Consume the iterator to trigger log printing
            list(invocation.wait())

        output = captured_output.getvalue()

        # Verify logs were printed to stdout
        assert "=== Step: Clone git repository ===" in output
        assert "Cloning into '/tmp/jobs/12345/target'..." in output
        assert "=== Step: Invoke dbt with `dbt build` ===" in output
        assert "15:49:32  Running dbt..." in output
