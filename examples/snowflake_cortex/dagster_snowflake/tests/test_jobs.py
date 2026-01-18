"""Test Dagster jobs."""

from dagster_snowflake_ai.defs.jobs import (
    daily_intelligence_job,
    weekly_reports_job,
)


class TestJobs:
    """Test job definitions."""

    def test_daily_intelligence_job(self):
        """Test daily intelligence job configuration."""
        assert daily_intelligence_job.name == "daily_intelligence"
        assert daily_intelligence_job.description is not None
        assert daily_intelligence_job.selection is not None

    def test_weekly_reports_job(self):
        """Test weekly reports job configuration."""
        assert weekly_reports_job.name == "weekly_reports"
        assert weekly_reports_job.description is not None
