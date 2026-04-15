"""Test run business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.graphql_adapter.run import process_runs_response
from dagster_rest_resources.schemas.run import DgApiRun, DgApiRunStatus


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
