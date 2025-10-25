"""Test schedule business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList
from dagster_dg_cli.cli.api.formatters import format_schedule, format_schedules


class TestFormatSchedules:
    """Test the schedule formatting functions."""

    def _create_sample_schedule_list(self):
        """Create sample DgApiScheduleList for testing."""
        schedules = [
            DgApiSchedule(
                id="schedule-1",
                name="daily_data_refresh",
                cron_schedule="0 2 * * *",
                pipeline_name="daily_data_job",
                description="Refreshes data tables daily at 2 AM",
                execution_timezone="UTC",
                tags=[
                    {"key": "team", "value": "data-platform"},
                    {"key": "priority", "value": "high"},
                ],
                metadata_entries=[
                    {"label": "owner", "description": "data-team"},
                    {
                        "label": "slack_channel",
                        "description": "#data-alerts",
                        "text": "#data-alerts",
                    },
                ],
            ),
            DgApiSchedule(
                id="schedule-2",
                name="hourly_metrics",
                cron_schedule="0 * * * *",
                pipeline_name="metrics_job",
                description="Calculates hourly metrics",
                execution_timezone="America/New_York",
                tags=[],
                metadata_entries=[],
            ),
        ]
        return DgApiScheduleList(items=schedules)

    def _create_empty_schedule_list(self):
        """Create empty DgApiScheduleList for testing."""
        return DgApiScheduleList(items=[])

    def _create_single_schedule(self):
        """Create single DgApiSchedule for testing."""
        return DgApiSchedule(
            id="schedule-1",
            name="daily_reports",
            cron_schedule="0 8 * * 1-5",
            pipeline_name="reporting_job",
            description="Generates daily reports on weekdays",
            execution_timezone="America/Los_Angeles",
            tags=[
                {"key": "environment", "value": "production"},
                {"key": "cost_center", "value": "analytics"},
            ],
            metadata_entries=[
                {
                    "label": "documentation",
                    "description": "Wiki link",
                    "url": "https://wiki.company.com/reports",
                },
                {"label": "run_timeout", "description": "Max runtime", "intValue": 3600},
                {
                    "label": "retry_policy",
                    "description": "Retry config",
                    "jsonString": '{"max_retries": 3, "delay": "30s"}',
                },
            ],
        )

    def test_format_schedules_text_output(self, snapshot):
        """Test formatting schedules as text."""
        schedule_list = self._create_sample_schedule_list()
        result = format_schedules(schedule_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_schedules_json_output(self, snapshot):
        """Test formatting schedules as JSON."""
        schedule_list = self._create_sample_schedule_list()
        result = format_schedules(schedule_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        import json

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

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_schedule_text_output(self, snapshot):
        """Test formatting single schedule as text."""
        schedule = self._create_single_schedule()
        result = format_schedule(schedule, as_json=False)

        snapshot.assert_match(result)

    def test_format_single_schedule_json_output(self, snapshot):
        """Test formatting single schedule as JSON."""
        schedule = self._create_single_schedule()
        result = format_schedule(schedule, as_json=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_schedule_without_metadata(self, snapshot):
        """Test formatting schedule with no metadata or tags."""
        schedule = DgApiSchedule(
            id="simple-schedule",
            name="simple_job",
            cron_schedule="0 0 * * *",
            pipeline_name="simple_pipeline",
            description=None,
            execution_timezone="UTC",
            tags=[],
            metadata_entries=[],
        )
        result = format_schedule(schedule, as_json=False)

        snapshot.assert_match(result)

    def test_format_schedule_pipeline_to_job_name_conversion(self, snapshot):
        """Test that pipeline_name is displayed as 'Job Name' in output."""
        schedule = DgApiSchedule(
            id="pipeline-test",
            name="test_schedule",
            cron_schedule="0 0 * * *",
            pipeline_name="my_pipeline_name",  # This should show as "Job Name" in output
            description="Test pipeline name conversion",
            execution_timezone="UTC",
            tags=[],
            metadata_entries=[],
        )
        result = format_schedule(schedule, as_json=False)

        # Verify "Job Name" appears instead of "Pipeline Name"
        assert "Job Name: my_pipeline_name" in result
        assert "Pipeline Name" not in result

        snapshot.assert_match(result)


class TestScheduleDataProcessing:
    """Test processing of schedule data structures.

    This class tests any pure functions related to schedule data processing
    and model creation.
    """

    def test_schedule_creation_with_complex_metadata(self, snapshot):
        """Test creating schedule with various metadata types."""
        schedule = DgApiSchedule(
            id="complex-schedule",
            name="complex_analytics_job",
            cron_schedule="0 2,14 * * *",  # Twice daily
            pipeline_name="analytics_pipeline",
            description="Complex schedule with various metadata types",
            execution_timezone="Europe/London",
            tags=[
                {"key": "team", "value": "data-engineering"},
                {"key": "sla", "value": "4h"},
                {"key": "cost_center", "value": "engineering"},
            ],
            metadata_entries=[
                {"label": "text_meta", "description": "Some text", "text": "example_text"},
                {
                    "label": "url_meta",
                    "description": "Documentation",
                    "url": "https://docs.example.com/schedules/complex",
                },
                {
                    "label": "path_meta",
                    "description": "Config file path",
                    "path": "/etc/dagster/schedules/complex.yaml",
                },
                {
                    "label": "json_meta",
                    "description": "Config",
                    "jsonString": '{"timeout": 3600, "retries": 3}',
                },
                {
                    "label": "markdown_meta",
                    "description": "Schedule notes",
                    "mdStr": "# Analytics Schedule\n\nRuns twice daily for analytics processing",
                },
                {
                    "label": "python_meta",
                    "description": "Handler class",
                    "module": "analytics.schedules",
                    "name": "ComplexScheduleHandler",
                },
                {"label": "float_meta", "description": "Success rate", "floatValue": 99.9},
                {"label": "int_meta", "description": "Average runtime", "intValue": 1800},
                {"label": "bool_meta", "description": "Auto retry enabled", "boolValue": True},
            ],
        )

        # Test JSON serialization works correctly
        result = schedule.model_dump_json(indent=2)
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_schedule_with_complex_cron_expressions(self):
        """Test schedule creation with various cron expressions."""
        test_cases = [
            ("0 0 * * *", "daily_midnight"),
            ("0 */2 * * *", "every_two_hours"),
            ("0 9-17 * * 1-5", "business_hours_weekdays"),
            ("15 2 1 * *", "monthly_first_day"),
            ("0 0 * * SUN", "weekly_sunday"),
        ]

        for cron_expression, name in test_cases:
            schedule = DgApiSchedule(
                id=f"schedule-{name}",
                name=name,
                cron_schedule=cron_expression,
                pipeline_name=f"{name}_job",
                description=f"Schedule with cron: {cron_expression}",
                execution_timezone="UTC",
                tags=[],
                metadata_entries=[],
            )

            assert schedule.cron_schedule == cron_expression
            assert schedule.name == name

    def test_schedule_timezone_handling(self):
        """Test schedule creation with different timezones."""
        timezones = [
            "UTC",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]

        for tz in timezones:
            schedule = DgApiSchedule(
                id=f"schedule-{tz.replace('/', '-')}",
                name=f"schedule_in_{tz.replace('/', '_')}",
                cron_schedule="0 9 * * *",
                pipeline_name="timezone_test_job",
                description=f"Schedule in {tz}",
                execution_timezone=tz,
                tags=[],
                metadata_entries=[],
            )

            assert schedule.execution_timezone == tz
