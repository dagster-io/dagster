from __future__ import annotations

from datetime import datetime

import dagster as dg

from harbor_outfitters.jobs import harbor_catalog_publish_job


def _schedule_tags(context: dg.ScheduleEvaluationContext) -> dict[str, str]:
    scheduled_time = context.scheduled_execution_time or datetime.now()
    orchestration_date = scheduled_time.date().isoformat()
    return {
        # Beacon's cross-location sensor uses this tag to correlate same-day upstream runs.
        "orchestration_date": orchestration_date,
        "tenant": "harbor_outfitters",
        "pipeline_stage": "publish",
    }


harbor_daily_refresh_schedule = dg.ScheduleDefinition(
    name="harbor_daily_refresh_schedule",
    job=harbor_catalog_publish_job,
    cron_schedule="0 9 * * *",
    execution_timezone="America/New_York",
    tags_fn=_schedule_tags,
    default_status=dg.DefaultScheduleStatus.STOPPED,
    description="Daily Harbor Outfitters refresh for retail context engineering and catalog publishing.",
)
