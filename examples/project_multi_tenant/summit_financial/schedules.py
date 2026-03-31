from __future__ import annotations

from datetime import datetime

import dagster as dg

from summit_financial.jobs import summit_risk_scoring_job


def _schedule_tags(context: dg.ScheduleEvaluationContext) -> dict[str, str]:
    scheduled_time = context.scheduled_execution_time or datetime.now()
    orchestration_date = scheduled_time.date().isoformat()
    return {
        # Beacon's cross-location sensor uses this tag to correlate same-day upstream runs.
        "orchestration_date": orchestration_date,
        "tenant": "summit_financial",
        "pipeline_stage": "risk_scoring",
    }


summit_daily_refresh_schedule = dg.ScheduleDefinition(
    name="summit_daily_refresh_schedule",
    job=summit_risk_scoring_job,
    cron_schedule="5 9 * * *",
    execution_timezone="America/New_York",
    tags_fn=_schedule_tags,
    default_status=dg.DefaultScheduleStatus.STOPPED,
    description="Daily Summit Financial refresh for investigation context and risk scoring.",
)
