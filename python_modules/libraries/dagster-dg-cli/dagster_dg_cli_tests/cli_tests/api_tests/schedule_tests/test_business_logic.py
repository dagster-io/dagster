"""Test schedule business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_schedule, format_schedules
from dagster_rest_resources.schemas.enums import DgApiInstigationStatus
from dagster_rest_resources.schemas.schedule import DgApiSchedule, DgApiScheduleList


class TestFormatSchedules:
    """Test the schedule formatting functions."""

    def _create_sample_schedule_list(self):
        """Create sample DgApiScheduleList for testing."""
        schedules = [
            DgApiSchedule(
                id="schedule1-id",
                name="daily_job",
                status=DgApiInstigationStatus.RUNNING,
                cron_schedule="0 0 * * *",
                pipeline_name="daily_pipeline",
                description="Runs daily at midnight",
                execution_timezone="UTC",
                code_location_origin="main_location@main_repo",
                next_tick_timestamp=1705311000.0,  # 2024-01-15T10:30:00Z
            ),
            DgApiSchedule(
                id="schedule2-id",
                name="hourly_job",
                status=DgApiInstigationStatus.STOPPED,
                cron_schedule="0 * * * *",
                pipeline_name="hourly_pipeline",
                description="Runs every hour",
                execution_timezone="America/New_York",
                code_location_origin="main_location@main_repo",
                next_tick_timestamp=None,
            ),
            DgApiSchedule(
                id="schedule3-id",
                name="minimal_schedule",
                status=DgApiInstigationStatus.RUNNING,
                cron_schedule="*/5 * * * *",
                pipeline_name="quick_job",
                description=None,
                execution_timezone=None,
                code_location_origin="test_location@test_repo",
                next_tick_timestamp=None,
            ),
        ]
        return DgApiScheduleList(items=schedules)

    def _create_empty_schedule_list(self):
        """Create empty DgApiScheduleList for testing."""
        return DgApiScheduleList(items=[])

    def _create_single_schedule(self):
        """Create single DgApiSchedule for testing."""
        return DgApiSchedule(
            id="single-schedule-id",
            name="critical_job",
            status=DgApiInstigationStatus.RUNNING,
            cron_schedule="0 0 * * *",
            pipeline_name="critical_pipeline",
            description="Critical production schedule",
            execution_timezone="UTC",
            code_location_origin="prod_location@prod_repo",
            next_tick_timestamp=1705311900.0,  # 2024-01-15T10:45:00Z
        )

    def test_format_schedules_text_output(self, snapshot):
        """Test formatting schedules as text."""
        from dagster_shared.utils.timing import fixed_timezone

        schedule_list = self._create_sample_schedule_list()
        with fixed_timezone("UTC"):
            result = format_schedules(schedule_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_schedules_json_output(self, snapshot):
        """Test formatting schedules as JSON."""
        schedule_list = self._create_sample_schedule_list()
        result = format_schedules(schedule_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_schedules_text_output(self, snapshot):
        """Test formatting empty schedule list as text."""
        schedule_list = self._create_empty_schedule_list()
        result = format_schedules(schedule_list, as_json=False)

        snapshot.assert_match(result)

    def test_format_empty_schedules_json_output(self, snapshot):
        """Test formatting empty schedule list as JSON."""
        schedule_list = self._create_empty_schedule_list()
        result = format_schedules(schedule_list, as_json=True)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_schedule_text_output(self, snapshot):
        """Test formatting single schedule as text."""
        from dagster_shared.utils.timing import fixed_timezone

        schedule = self._create_single_schedule()
        with fixed_timezone("UTC"):
            result = format_schedule(schedule, as_json=False)

        # Snapshot the text output
        snapshot.assert_match(result)

    def test_format_single_schedule_json_output(self, snapshot):
        """Test formatting single schedule as JSON."""
        schedule = self._create_single_schedule()
        result = format_schedule(schedule, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_schedule_text_output(self, snapshot):
        """Test formatting minimal schedule as text."""
        from dagster_shared.utils.timing import fixed_timezone

        schedule = DgApiSchedule(
            id="minimal-id",
            name="minimal_schedule",
            status=DgApiInstigationStatus.STOPPED,
            cron_schedule="*/15 * * * *",
            pipeline_name="minimal_pipeline",
            description=None,
            execution_timezone=None,
            code_location_origin="test_location@test_repo",
            next_tick_timestamp=None,
        )
        with fixed_timezone("UTC"):
            result = format_schedule(schedule, as_json=False)

        snapshot.assert_match(result)

    def test_format_minimal_schedule_json_output(self, snapshot):
        """Test formatting minimal schedule as JSON."""
        schedule = DgApiSchedule(
            id="minimal-id",
            name="minimal_schedule",
            status=DgApiInstigationStatus.STOPPED,
            cron_schedule="*/15 * * * *",
            pipeline_name="minimal_pipeline",
            description=None,
            execution_timezone=None,
            code_location_origin="test_location@test_repo",
            next_tick_timestamp=None,
        )
        result = format_schedule(schedule, as_json=True)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)
