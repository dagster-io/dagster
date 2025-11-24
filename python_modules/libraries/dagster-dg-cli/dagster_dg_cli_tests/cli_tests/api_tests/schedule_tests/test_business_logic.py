"""Test schedule business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.graphql_adapter.schedule import (
    process_repositories_response,
    process_schedule_response,
    process_schedules_response,
)
from dagster_dg_cli.api_layer.schemas.schedule import (
    DgApiSchedule,
    DgApiScheduleList,
    DgApiScheduleStatus,
)
from dagster_dg_cli.cli.api.schedule import format_schedule, format_schedules


class TestProcessScheduleResponses:
    """Test the pure functions that process GraphQL responses."""

    def test_process_schedules_response_success(self, snapshot):
        """Test processing a successful schedules GraphQL response."""
        # Sample GraphQL response structure
        response = {
            "schedulesOrError": {
                "__typename": "Schedules",
                "results": [
                    {
                        "id": "schedule1-id",
                        "name": "daily_job",
                        "cronSchedule": "0 0 * * *",
                        "pipelineName": "daily_pipeline",
                        "description": "Runs daily at midnight",
                        "executionTimezone": "UTC",
                        "scheduleState": {"status": "RUNNING"},
                    },
                    {
                        "id": "schedule2-id",
                        "name": "hourly_job",
                        "cronSchedule": "0 * * * *",
                        "pipelineName": "hourly_pipeline",
                        "description": "Runs every hour",
                        "executionTimezone": "America/New_York",
                        "scheduleState": {"status": "STOPPED"},
                    },
                ],
            }
        }
        result = process_schedules_response(response)

        # Snapshot the entire result to capture structure and data
        snapshot.assert_match(result)

    def test_process_schedules_response_empty(self, snapshot):
        """Test processing an empty schedules GraphQL response."""
        response = {"schedulesOrError": {"__typename": "Schedules", "results": []}}
        result = process_schedules_response(response)

        # Snapshot empty result
        snapshot.assert_match(result)

    def test_process_schedules_response_missing_key(self, snapshot):
        """Test processing a response missing the schedulesOrError key."""
        malformed_response = {}
        try:
            result = process_schedules_response(malformed_response)
            # If no exception, snapshot the result
            snapshot.assert_match(result)
        except Exception as e:
            # Snapshot the error message
            snapshot.assert_match({"error": str(e)})

    def test_process_schedules_response_error_typename(self, snapshot):
        """Test processing a schedules response with error typename."""
        error_response = {
            "schedulesOrError": {
                "__typename": "RepositoryNotFoundError",
                "message": "Repository not found",
            }
        }
        try:
            result = process_schedules_response(error_response)
            snapshot.assert_match(result)
        except Exception as e:
            snapshot.assert_match({"error": str(e)})

    def test_process_repositories_response_success(self, snapshot):
        """Test processing a successful repositories GraphQL response."""
        response = {
            "repositoriesOrError": {
                "__typename": "RepositoryConnection",
                "nodes": [
                    {
                        "name": "main_repo",
                        "location": {"name": "main_location"},
                        "schedules": [
                            {
                                "id": "schedule1-id",
                                "name": "daily_job",
                                "cronSchedule": "0 0 * * *",
                                "pipelineName": "daily_pipeline",
                                "description": "Runs daily at midnight",
                                "executionTimezone": "UTC",
                                "scheduleState": {"status": "RUNNING"},
                            },
                            {
                                "id": "schedule2-id",
                                "name": "weekly_job",
                                "cronSchedule": "0 0 * * 0",
                                "pipelineName": "weekly_pipeline",
                                "description": "Runs weekly on Sunday",
                                "executionTimezone": None,
                                "scheduleState": {"status": "STOPPED"},
                            },
                        ],
                    },
                    {
                        "name": "secondary_repo",
                        "location": {"name": "secondary_location"},
                        "schedules": [
                            {
                                "id": "schedule3-id",
                                "name": "hourly_job",
                                "cronSchedule": "0 * * * *",
                                "pipelineName": "hourly_pipeline",
                                "description": None,
                                "executionTimezone": "America/Chicago",
                                "scheduleState": {"status": "RUNNING"},
                            }
                        ],
                    },
                ],
            }
        }
        result = process_repositories_response(response)

        # Snapshot the entire result to capture structure and data
        snapshot.assert_match(result)

    def test_process_repositories_response_empty(self, snapshot):
        """Test processing an empty repositories GraphQL response."""
        response = {"repositoriesOrError": {"__typename": "RepositoryConnection", "nodes": []}}
        result = process_repositories_response(response)

        snapshot.assert_match(result)

    def test_process_schedule_response_success(self, snapshot):
        """Test processing a successful single schedule GraphQL response."""
        response = {
            "scheduleOrError": {
                "__typename": "Schedule",
                "id": "single-schedule-id",
                "name": "critical_job",
                "cronSchedule": "0 0 * * *",
                "pipelineName": "critical_pipeline",
                "description": "Critical production schedule",
                "executionTimezone": "UTC",
                "scheduleState": {"status": "RUNNING"},
            }
        }
        result = process_schedule_response(response)

        snapshot.assert_match(result)

    def test_process_schedule_response_not_found_error(self, snapshot):
        """Test processing a schedule not found error."""
        error_response = {
            "scheduleOrError": {
                "__typename": "ScheduleNotFoundError",
                "message": "Schedule 'nonexistent_schedule' not found",
            }
        }
        try:
            result = process_schedule_response(error_response)
            snapshot.assert_match(result)
        except Exception as e:
            snapshot.assert_match({"error": str(e)})


class TestFormatSchedules:
    """Test the schedule formatting functions."""

    def _create_sample_schedule_list(self):
        """Create sample DgApiScheduleList for testing."""
        schedules = [
            DgApiSchedule(
                id="schedule1-id",
                name="daily_job",
                status=DgApiScheduleStatus.RUNNING,
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
                status=DgApiScheduleStatus.STOPPED,
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
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="*/5 * * * *",
                pipeline_name="quick_job",
                description=None,
                execution_timezone=None,
                code_location_origin=None,
                next_tick_timestamp=None,
            ),
        ]
        return DgApiScheduleList(items=schedules, total=len(schedules))

    def _create_empty_schedule_list(self):
        """Create empty DgApiScheduleList for testing."""
        return DgApiScheduleList(items=[], total=0)

    def _create_single_schedule(self):
        """Create single DgApiSchedule for testing."""
        return DgApiSchedule(
            id="single-schedule-id",
            name="critical_job",
            status=DgApiScheduleStatus.RUNNING,
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
            status=DgApiScheduleStatus.STOPPED,
            cron_schedule="*/15 * * * *",
            pipeline_name="minimal_pipeline",
            description=None,
            execution_timezone=None,
            code_location_origin=None,
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
            status=DgApiScheduleStatus.STOPPED,
            cron_schedule="*/15 * * * *",
            pipeline_name="minimal_pipeline",
            description=None,
            execution_timezone=None,
            code_location_origin=None,
            next_tick_timestamp=None,
        )
        result = format_schedule(schedule, as_json=True)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestScheduleDataProcessing:
    """Test processing of schedule data structures.

    This class tests pure functions and domain model functionality
    without requiring external dependencies.
    """

    def test_schedule_creation_with_all_fields(self, snapshot):
        """Test creating schedule with all possible fields."""
        schedule = DgApiSchedule(
            id="complete-schedule-xyz",
            name="comprehensive_schedule",
            status=DgApiScheduleStatus.RUNNING,
            cron_schedule="0 0 * * *",
            pipeline_name="comprehensive_pipeline",
            description="Comprehensive test schedule with all fields",
            execution_timezone="America/Los_Angeles",
            code_location_origin="test_location@test_repo",
            next_tick_timestamp=1705311000.0,
        )

        # Test JSON serialization works correctly
        result = schedule.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_schedule_status_enum_values(self):
        """Test that all expected ScheduleStatus enum values are available."""
        expected_statuses = ["RUNNING", "STOPPED"]

        actual_statuses = [status.value for status in DgApiScheduleStatus]
        assert set(actual_statuses) == set(expected_statuses)

    def test_schedule_with_missing_optional_fields(self):
        """Test schedule creation with None values for optional fields."""
        schedule = DgApiSchedule(
            id="sparse-schedule-123",
            name="sparse_schedule",
            status=DgApiScheduleStatus.STOPPED,
            cron_schedule="0 12 * * *",
            pipeline_name="sparse_pipeline",
            description=None,
            execution_timezone=None,
            code_location_origin=None,
            next_tick_timestamp=None,
        )

        assert schedule.id == "sparse-schedule-123"
        assert schedule.name == "sparse_schedule"
        assert schedule.status == DgApiScheduleStatus.STOPPED
        assert schedule.cron_schedule == "0 12 * * *"
        assert schedule.pipeline_name == "sparse_pipeline"
        assert schedule.description is None
        assert schedule.execution_timezone is None
        assert schedule.code_location_origin is None
        assert schedule.next_tick_timestamp is None

    def test_schedule_list_creation(self):
        """Test ScheduleList creation and basic functionality."""
        schedules = [
            DgApiSchedule(
                id="schedule1",
                name="first_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 0 * * *",
                pipeline_name="first_pipeline",
            ),
            DgApiSchedule(
                id="schedule2",
                name="second_schedule",
                status=DgApiScheduleStatus.STOPPED,
                cron_schedule="0 6 * * *",
                pipeline_name="second_pipeline",
            ),
        ]
        schedule_list = DgApiScheduleList(items=schedules, total=len(schedules))

        assert len(schedule_list.items) == 2
        assert schedule_list.total == 2
        assert schedule_list.items[0].name == "first_schedule"
        assert schedule_list.items[1].name == "second_schedule"

    def test_schedule_timestamp_handling(self, snapshot):
        """Test schedule with various timestamp values."""
        test_cases = [
            # Normal timestamp
            DgApiSchedule(
                id="schedule1",
                name="normal_timestamp",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 0 * * *",
                pipeline_name="normal_pipeline",
                next_tick_timestamp=1705311000.0,
            ),
            # No timestamp
            DgApiSchedule(
                id="schedule2",
                name="no_timestamp",
                status=DgApiScheduleStatus.STOPPED,
                cron_schedule="0 12 * * *",
                pipeline_name="no_pipeline",
                next_tick_timestamp=None,
            ),
            # Future timestamp
            DgApiSchedule(
                id="schedule3",
                name="future_timestamp",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 18 * * *",
                pipeline_name="future_pipeline",
                next_tick_timestamp=2000000000.0,  # Far future
            ),
        ]

        results = []
        for schedule in test_cases:
            # Test serialization
            serialized = json.loads(schedule.model_dump_json())
            results.append(serialized)

        snapshot.assert_match(results)

    def test_schedule_cron_patterns(self, snapshot):
        """Test schedules with various cron patterns."""
        test_cases = [
            # Daily at midnight
            DgApiSchedule(
                id="daily",
                name="daily_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 0 * * *",
                pipeline_name="daily_pipeline",
            ),
            # Hourly
            DgApiSchedule(
                id="hourly",
                name="hourly_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 * * * *",
                pipeline_name="hourly_pipeline",
            ),
            # Every 15 minutes
            DgApiSchedule(
                id="frequent",
                name="frequent_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="*/15 * * * *",
                pipeline_name="frequent_pipeline",
            ),
            # Weekly on Monday at 9am
            DgApiSchedule(
                id="weekly",
                name="weekly_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 9 * * 1",
                pipeline_name="weekly_pipeline",
            ),
            # Monthly on 1st at midnight
            DgApiSchedule(
                id="monthly",
                name="monthly_schedule",
                status=DgApiScheduleStatus.RUNNING,
                cron_schedule="0 0 1 * *",
                pipeline_name="monthly_pipeline",
            ),
        ]

        results = []
        for schedule in test_cases:
            serialized = json.loads(schedule.model_dump_json())
            results.append(serialized)

        snapshot.assert_match(results)
