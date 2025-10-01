"""Test run business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunStatus


def format_run_table(run) -> str:
    """Format run as human-readable table."""
    lines = [
        f"Run ID: {run.id}",
        f"Status: {run.status.value}",
        f"Created: {run.created_at}",
    ]

    if run.started_at:
        lines.append(f"Started: {run.started_at}")
    if run.ended_at:
        lines.append(f"Ended: {run.ended_at}")
    if run.job_name:
        lines.append(f"Pipeline: {run.job_name}")

    return "\n".join(lines)


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
        result = format_run_table(run)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_run_json_output(self, snapshot):
        """Test formatting run as JSON."""
        run = self._create_sample_run()
        result = run.model_dump_json(indent=2)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_run_text_output(self, snapshot):
        """Test formatting minimal run as text."""
        run = self._create_minimal_run()
        result = format_run_table(run)

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
        result = format_run_table(run)

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
        result = format_run_table(run)

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
