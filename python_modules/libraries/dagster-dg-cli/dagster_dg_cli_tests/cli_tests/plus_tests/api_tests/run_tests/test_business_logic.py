"""Test run business logic directly with recorded responses."""

import json

import pytest
from click import ClickException
from dagster_dg_cli.cli.plus.api.run.business_logic import (
    format_run_view_output,
    process_run_view_response,
)

from dagster_dg_cli_tests.cli_tests.plus_tests.api_tests.run_tests.fixtures.run_responses import (
    RUN_VIEW_ERROR_RESPONSE,
    RUN_VIEW_NOT_FOUND_RESPONSE,
    RUN_VIEW_SUCCESS_RESPONSE,
)


class TestProcessRunViewResponse:
    """Test GraphQL response processing logic."""

    def test_successful_response_processing(self):
        """Test processing a successful run response."""
        api_response = process_run_view_response(RUN_VIEW_SUCCESS_RESPONSE)

        # Test basic fields
        assert api_response["run_id"] == "9d38c7ea"
        assert api_response["status"] == "SUCCESS"
        assert api_response["job_name"] == "test_job"
        assert api_response["pipeline_name"] == "test_pipeline"

        # Test tags transformation
        assert isinstance(api_response["tags"], dict)
        assert api_response["tags"]["test_key"] == "test_value"

        # Test assets transformation
        assert isinstance(api_response["assets"], list)
        assert len(api_response["assets"]) == 1
        assert api_response["assets"][0] == ["test", "asset"]

        # Test stats transformation
        assert isinstance(api_response["stats"], dict)
        assert api_response["stats"]["steps_succeeded"] == 5
        assert api_response["stats"]["steps_failed"] == 0
        assert api_response["stats"]["materializations"] == 2

    def test_run_not_found_error(self):
        """Test handling of RunNotFoundError responses."""
        with pytest.raises(ClickException) as exc_info:
            process_run_view_response(RUN_VIEW_NOT_FOUND_RESPONSE)

        assert "Run not found" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_python_error_handling(self):
        """Test handling of PythonError responses."""
        with pytest.raises(ClickException) as exc_info:
            process_run_view_response(RUN_VIEW_ERROR_RESPONSE)

        assert "API Error" in str(exc_info.value)
        assert "Database connection failed" in str(exc_info.value)

    def test_empty_response_handling(self):
        """Test handling of empty/invalid responses."""
        with pytest.raises(ClickException) as exc_info:
            process_run_view_response({})

        assert "No run data returned from API" in str(exc_info.value)

    def test_missing_optional_fields(self):
        """Test handling of responses with missing optional fields."""
        minimal_response = {
            "runOrError": {
                "__typename": "Run",
                "id": "test-id",
                "runId": "test-run",
                "status": "SUCCESS",
                # Missing optional fields like tags, assets, stats
            }
        }

        api_response = process_run_view_response(minimal_response)

        assert api_response["run_id"] == "test-run"
        assert api_response["status"] == "SUCCESS"
        assert api_response["tags"] == {}
        assert api_response["assets"] == []
        assert api_response["stats"] == {}


class TestFormatRunViewOutput:
    """Test output formatting logic."""

    @pytest.fixture
    def sample_api_response(self):
        """Sample processed API response for testing."""
        return {
            "run_id": "9d38c7ea",
            "status": "SUCCESS",
            "job_name": "test_job",
            "tags": {"key1": "value1", "key2": "value2"},
            "assets": [["sling", "table1"], ["sling", "table2"]],
            "stats": {"steps_succeeded": 5, "steps_failed": 0},
        }

    def test_json_formatting(self, sample_api_response):
        """Test JSON output formatting."""
        output = format_run_view_output(sample_api_response, as_json=True)

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["run_id"] == "9d38c7ea"
        assert parsed["status"] == "SUCCESS"

        # Should be properly indented
        assert "\n" in output
        assert "  " in output  # Indentation spaces

    def test_human_readable_formatting(self, sample_api_response):
        """Test human-readable output formatting."""
        output = format_run_view_output(sample_api_response, as_json=False)

        # Should contain key information
        assert "run_id: 9d38c7ea" in output
        assert "status: SUCCESS" in output
        assert "job_name: test_job" in output

        # Lists should show count
        assert "assets: 2 items" in output

        # Should be newline-separated
        lines = output.split("\n")
        assert len(lines) > 1

    def test_empty_response_formatting(self):
        """Test formatting of empty response."""
        empty_response = {}

        # JSON format should work
        json_output = format_run_view_output(empty_response, as_json=True)
        assert json.loads(json_output) == {}

        # Human-readable should handle empty dict
        human_output = format_run_view_output(empty_response, as_json=False)
        assert human_output == ""  # No fields to display
