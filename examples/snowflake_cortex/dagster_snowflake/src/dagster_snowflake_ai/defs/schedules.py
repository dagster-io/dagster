"""Schedule definitions for Dagster."""

import dagster as dg

from dagster_snowflake_ai.defs.jobs import daily_intelligence_job, weekly_reports_job

daily_schedule = dg.ScheduleDefinition(
    job=daily_intelligence_job,
    cron_schedule="0 2 * * *",
    name="daily_intelligence_schedule",
    execution_timezone="America/New_York",
    description="Run daily Hacker News processing at 2 AM EST",
)

weekly_schedule = dg.ScheduleDefinition(
    job=weekly_reports_job,
    cron_schedule="0 3 * * 0",
    name="weekly_reports_schedule",
    execution_timezone="America/New_York",
    description="Run weekly comprehensive reports on Sunday at 3 AM EST",
)
