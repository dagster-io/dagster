"""Integration tests for bk-build-status command."""

import json
import os
from unittest.mock import Mock, patch

from click.testing import CliRunner


def create_mock_buildkite_response(jobs):
    """Create a mock Buildkite API response."""
    return {"jobs": jobs}


def create_mock_job(name, state, job_id=None):
    """Create a mock Buildkite job."""
    return {
        "id": job_id or f"job-{name.lower().replace(' ', '-')}",
        "name": name,
        "state": state,
    }


def mock_requests_get(mock_response_data):
    """Create a mock requests.get response."""
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestBkBuildStatus:
    """Test cases for the bk-build-status command."""

    def test_successful_build_status_with_build_number(self):
        """Test successful build status retrieval with explicit build number."""
        # Mock job data
        jobs = [
            create_mock_job("Unit Tests", "passed"),
            create_mock_job("Integration Tests", "running"),
            create_mock_job("Linting", "failed"),
        ]
        mock_response_data = create_mock_buildkite_response(jobs)

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.return_value = mock_requests_get(mock_response_data)

            # Set environment variable
            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345"])

                assert result.exit_code == 0
                assert "Build Status Summary for dagster/dagster-dagster #12345" in result.output
                assert "Passed Jobs (1 total)" in result.output
                assert "Unit Tests" in result.output
                assert "Running Jobs (1 total)" in result.output
                assert "Integration Tests" in result.output
                assert "Failed Jobs (1 total)" in result.output
                assert "Linting" in result.output
                assert "Action Required" in result.output

    def test_successful_build_status_json_output(self):
        """Test JSON output format."""
        jobs = [
            create_mock_job("Unit Tests", "passed", "job-1"),
            create_mock_job("Integration Tests", "running", "job-2"),
        ]
        mock_response_data = create_mock_buildkite_response(jobs)

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.return_value = mock_requests_get(mock_response_data)

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345", "--json"])

                assert result.exit_code == 0

                # Parse JSON output
                output_data = json.loads(result.output)
                assert output_data["build"]["number"] == "12345"
                assert output_data["summary"]["passed"] == 1
                assert output_data["summary"]["running"] == 1
                assert output_data["summary"]["failed"] == 0
                assert output_data["status"] == "running"
                assert len(output_data["jobs"]["passed"]) == 1
                assert len(output_data["jobs"]["running"]) == 1

    def test_build_status_auto_detect_from_pr(self):
        """Test build status with auto-detected build number from PR."""
        jobs = [create_mock_job("Unit Tests", "passed")]
        mock_response_data = create_mock_buildkite_response(jobs)

        with (
            patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get,
            patch(
                "automation.dagster_dev.commands.bk_build_status.get_latest_build_for_pr"
            ) as mock_get_build,
        ):
            mock_get.return_value = mock_requests_get(mock_response_data)
            mock_get_build.return_value = "54321"

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, [])

                assert result.exit_code == 0
                assert "detecting from current PR" in result.output
                assert "Build Status Summary for dagster/dagster-dagster #54321" in result.output
                mock_get_build.assert_called_once()

    def test_missing_buildkite_token(self):
        """Test error when BUILDKITE_API_TOKEN is not set."""
        with patch.dict(os.environ, {}, clear=True):
            from automation.dagster_dev.commands.bk_build_status import bk_build_status

            runner = CliRunner()
            result = runner.invoke(bk_build_status, ["12345"])

            assert result.exit_code == 1
            assert "BUILDKITE_API_TOKEN environment variable not set" in result.output

    def test_api_request_failure(self):
        """Test handling of Buildkite API request failure."""
        import requests

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345"])

                assert result.exit_code == 1
                assert "Error calling Buildkite API" in result.output

    def test_api_json_decode_error(self):
        """Test handling of invalid JSON response."""
        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345"])

                assert result.exit_code == 1
                assert "Error parsing JSON response" in result.output

    def test_custom_org_and_pipeline(self):
        """Test with custom organization and pipeline."""
        jobs = [create_mock_job("Test Job", "passed")]
        mock_response_data = create_mock_buildkite_response(jobs)

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.return_value = mock_requests_get(mock_response_data)

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(
                    bk_build_status, ["12345", "--org", "myorg", "--pipeline", "mypipeline"]
                )

                assert result.exit_code == 0
                assert "Build Status Summary for myorg/mypipeline #12345" in result.output

                # Verify correct API endpoint was called
                mock_get.assert_called_once()
                called_url = mock_get.call_args[0][0]
                assert "myorg" in called_url
                assert "mypipeline" in called_url

    def test_all_jobs_passed(self):
        """Test successful build with all jobs passed."""
        jobs = [
            create_mock_job("Unit Tests", "passed"),
            create_mock_job("Integration Tests", "passed"),
        ]
        mock_response_data = create_mock_buildkite_response(jobs)

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.return_value = mock_requests_get(mock_response_data)

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345"])

                assert result.exit_code == 0
                assert "Build completed successfully!" in result.output
                assert "(none)" in result.output  # For running and failed jobs

    def test_no_jobs_in_build(self):
        """Test build with no jobs."""
        mock_response_data = create_mock_buildkite_response([])

        with patch("automation.dagster_dev.commands.bk_build_status.requests.get") as mock_get:
            mock_get.return_value = mock_requests_get(mock_response_data)

            with patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "test-token"}):
                from automation.dagster_dev.commands.bk_build_status import bk_build_status

                runner = CliRunner()
                result = runner.invoke(bk_build_status, ["12345"])

                assert result.exit_code == 0
                assert "0 total active jobs" in result.output
