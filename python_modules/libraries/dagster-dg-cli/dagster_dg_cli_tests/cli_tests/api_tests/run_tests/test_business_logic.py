"""Test run business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_run, format_runs_list
from dagster_rest_resources.schemas.run import DgApiRun, DgApiRunList, DgApiRunStatus
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
