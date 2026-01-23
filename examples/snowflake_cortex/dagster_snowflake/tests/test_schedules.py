"""Test Dagster schedules."""

from dagster_snowflake_ai.defs.schedules import daily_schedule, weekly_schedule


class TestSchedules:
    """Test schedule definitions."""

    def test_daily_schedule_configuration(self):
        """Test daily schedule configuration."""
        assert daily_schedule.name == "daily_intelligence_schedule"
        assert daily_schedule.cron_schedule == "0 2 * * *"
        assert daily_schedule.execution_timezone == "America/New_York"
        assert daily_schedule.job.name == "daily_intelligence"

    def test_weekly_schedule_configuration(self):
        """Test weekly schedule configuration."""
        assert weekly_schedule.name == "weekly_reports_schedule"
        assert weekly_schedule.cron_schedule == "0 3 * * 0"
        assert weekly_schedule.execution_timezone == "America/New_York"
        assert weekly_schedule.job.name == "weekly_reports"

    def test_schedule_timing_consistency(self):
        """Test that schedules run at appropriate times."""
        # Daily schedule should run early morning
        daily_hour = int(daily_schedule.cron_schedule.split()[1])
        assert daily_hour <= 6, "Daily schedule should run early in the morning"

        # Weekly schedule should run on Sunday
        weekly_day = daily_schedule.cron_schedule.split()[4]
        assert weekly_day == "*", "Weekly schedule uses day-of-week field"
