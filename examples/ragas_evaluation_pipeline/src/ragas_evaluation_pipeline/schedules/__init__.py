"""Periodic evaluation schedule (Point 8).

Runs the full evaluation daily so RAG quality is tracked as a recurring pipeline
artifact rather than a one-off script.
"""

from dagster import ScheduleDefinition

from ragas_evaluation_pipeline.jobs import evaluation_job

evaluation_daily_schedule = ScheduleDefinition(
    name="evaluation_daily_schedule",
    job=evaluation_job,
    cron_schedule="0 9 * * *",  # every day at 09:00
)
