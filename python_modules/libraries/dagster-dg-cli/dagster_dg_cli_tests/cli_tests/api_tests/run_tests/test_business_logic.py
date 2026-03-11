"""Test run business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.graphql_adapter.run import process_runs_response
from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunList, DgApiRunStatus
from dagster_dg_cli.cli.api.formatters import format_run, format_runs_list
from dagster_shared.utils.timing import fixed_timezone


class TestFormatRun:
    """Test the run formatting functions."""

    def _create_sample_run(self):
        """Create sample Run for testing."""
        return DgApiRun(
            id="123e4567-e89b-12d3-a456-426614174000",
            status=DgApiRunStatus.SUCCESS,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=1705311900.0,  # 2024-01-15T10:45:00Z
            job_name="my_pipeline",
        )

    def _create_minimal_run(self):
        """Create minimal Run with only required fields."""
        return DgApiRun(
            id="minimal-run-123",
            status=DgApiRunStatus.QUEUED,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
        )

    def _create_failed_run(self):
        """Create failed Run for testing."""
        return DgApiRun(
            id="failed-run-456",
            status=DgApiRunStatus.FAILURE,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=1705311180.0,  # 2024-01-15T10:33:00Z
            job_name="failing_pipeline",
        )

    def _create_canceled_run(self):
        """Create canceled Run for testing."""
        return DgApiRun(
            id="canceled-run-789",
            status=DgApiRunStatus.CANCELED,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=1705311120.0,  # 2024-01-15T10:32:00Z
            job_name="canceled_pipeline",
        )

    def test_format_run_text_output(self, snapshot):
        """Test formatting run as text."""
        run = self._create_sample_run()
        with fixed_timezone("UTC"):
            result = format_run(run, as_json=False)

        snapshot.assert_match(result)

    def test_format_run_json_output(self, snapshot):
        """Test formatting run as JSON."""
        run = self._create_sample_run()
        result = run.model_dump_json(indent=2)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_run_text_output(self, snapshot):
        """Test formatting minimal run as text."""
        run = self._create_minimal_run()
        with fixed_timezone("UTC"):
            result = format_run(run, as_json=False)

        snapshot.assert_match(result)

    def test_format_minimal_run_json_output(self, snapshot):
        """Test formatting minimal run as JSON."""
        run = self._create_minimal_run()
        result = run.model_dump_json(indent=2)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_failed_run_text_output(self, snapshot):
        """Test formatting failed run as text."""
        run = self._create_failed_run()
        with fixed_timezone("UTC"):
            result = format_run(run, as_json=False)

        snapshot.assert_match(result)

    def test_format_failed_run_json_output(self, snapshot):
        """Test formatting failed run as JSON."""
        run = self._create_failed_run()
        result = run.model_dump_json(indent=2)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_canceled_run_text_output(self, snapshot):
        """Test formatting canceled run as text."""
        run = self._create_canceled_run()
        with fixed_timezone("UTC"):
            result = format_run(run, as_json=False)

        snapshot.assert_match(result)

    def test_format_canceled_run_json_output(self, snapshot):
        """Test formatting canceled run as JSON."""
        run = self._create_canceled_run()
        result = run.model_dump_json(indent=2)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestRunDataProcessing:
    """Test processing of run data structures.

    This class would test any pure functions in the GraphQL adapter
    that process the raw GraphQL responses into our domain models.
    """

    def test_run_creation_with_all_fields(self, snapshot):
        """Test creating run with all possible fields."""
        run = DgApiRun(
            id="complete-run-xyz",
            status=DgApiRunStatus.STARTING,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=1705311060.0,  # 2024-01-15T10:31:00Z
            ended_at=None,  # Still running
            job_name="comprehensive_pipeline",
        )

        # Test JSON serialization works correctly
        result = run.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_run_status_enum_values(self):
        """Test that all expected RunStatus enum values are available."""
        expected_statuses = [
            "QUEUED",
            "STARTING",
            "STARTED",
            "SUCCESS",
            "FAILURE",
            "CANCELING",
            "CANCELED",
        ]

        actual_statuses = [status.value for status in DgApiRunStatus]
        assert set(actual_statuses) == set(expected_statuses)

    def test_run_with_missing_optional_fields(self):
        """Test run creation with None values for optional fields."""
        run = DgApiRun(
            id="sparse-run-123",
            status=DgApiRunStatus.QUEUED,
            created_at=1705311000.0,  # 2024-01-15T10:30:00Z
            started_at=None,
            ended_at=None,
            job_name=None,
        )

        assert run.id == "sparse-run-123"
        assert run.status == DgApiRunStatus.QUEUED
        assert run.created_at == 1705311000.0
        assert run.started_at is None
        assert run.ended_at is None
        assert run.job_name is None


class TestFormatRunsList:
    """Test the runs list formatting functions."""

    def _create_sample_runs_list(self) -> DgApiRunList:
        """Create sample RunList for testing."""
        return DgApiRunList(
            items=[
                DgApiRun(
                    id="run-001",
                    status=DgApiRunStatus.SUCCESS,
                    created_at=1705311000.0,
                    started_at=1705311060.0,
                    ended_at=1705311900.0,
                    job_name="my_pipeline",
                ),
                DgApiRun(
                    id="run-002",
                    status=DgApiRunStatus.FAILURE,
                    created_at=1705312000.0,
                    started_at=1705312060.0,
                    ended_at=1705312180.0,
                    job_name="failing_pipeline",
                ),
                DgApiRun(
                    id="run-003",
                    status=DgApiRunStatus.QUEUED,
                    created_at=1705313000.0,
                    job_name=None,
                ),
            ],
        )

    def test_format_runs_list_text(self, snapshot):
        """Test formatting runs list as text."""
        runs_list = self._create_sample_runs_list()
        with fixed_timezone("UTC"):
            result = format_runs_list(runs_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_runs_list_json(self, snapshot):
        """Test formatting runs list as JSON."""
        runs_list = self._create_sample_runs_list()
        result = format_runs_list(runs_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_runs_list_empty_text(self, snapshot):
        """Test formatting empty runs list as text."""
        runs_list = DgApiRunList(items=[])
        result = format_runs_list(runs_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_runs_list_empty_json(self, snapshot):
        """Test formatting empty runs list as JSON."""
        runs_list = DgApiRunList(items=[])
        result = format_runs_list(runs_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestProcessRunsResponse:
    """Test the process_runs_response pure function."""

    def test_process_runs_response_success(self):
        """Test processing a successful GraphQL response."""
        graphql_response = {
            "runsOrError": {
                "__typename": "Runs",
                "results": [
                    {
                        "runId": "abc-123",
                        "status": "SUCCESS",
                        "creationTime": 1705311000.0,
                        "startTime": 1705311060.0,
                        "endTime": 1705311900.0,
                        "jobName": "my_job",
                    },
                    {
                        "runId": "def-456",
                        "status": "QUEUED",
                        "creationTime": 1705312000.0,
                        "startTime": None,
                        "endTime": None,
                        "jobName": None,
                    },
                ],
            }
        }

        result = process_runs_response(graphql_response)

        assert len(result.items) == 2
        assert result.items[0].id == "abc-123"
        assert result.items[0].status == DgApiRunStatus.SUCCESS
        assert result.items[0].job_name == "my_job"
        assert result.items[1].id == "def-456"
        assert result.items[1].status == DgApiRunStatus.QUEUED

    def test_process_runs_response_empty(self):
        """Test processing an empty results response."""
        graphql_response = {
            "runsOrError": {
                "__typename": "Runs",
                "results": [],
            }
        }

        result = process_runs_response(graphql_response)

        assert len(result.items) == 0

    def test_process_runs_response_python_error(self):
        """Test processing a PythonError response."""
        import pytest

        graphql_response = {
            "runsOrError": {
                "__typename": "PythonError",
                "message": "Something went wrong",
                "stack": ["traceback line 1"],
            }
        }

        with pytest.raises(Exception, match="GraphQL error: Something went wrong"):
            process_runs_response(graphql_response)
