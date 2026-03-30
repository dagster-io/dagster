from __future__ import annotations

from datetime import datetime, timezone

import dagster as dg

from beacon_hq.jobs import beacon_executive_briefing_job

UPSTREAM_JOB_NAMES = {
    "harbor_catalog_publish_job",
    "summit_risk_scoring_job",
}


def _orchestration_date_for_run(
    instance: dg.DagsterInstance,
    dagster_run: dg.DagsterRun,
) -> str | None:
    tagged_date = dagster_run.tags.get("orchestration_date")
    if tagged_date:
        return tagged_date

    record = instance.get_run_record_by_id(dagster_run.run_id)
    if record is None:
        return None

    event_time = record.start_time or record.create_timestamp.timestamp()
    return datetime.fromtimestamp(event_time, tz=timezone.utc).date().isoformat()


@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.SUCCESS,
    name="beacon_after_upstream_success_sensor",
    monitor_all_code_locations=True,
    request_job=beacon_executive_briefing_job,
    default_status=dg.DefaultSensorStatus.STOPPED,
    description=(
        "Launch Beacon HQ's executive briefing after both Harbor Outfitters and Summit Financial succeed for the same "
        "orchestration date."
    ),
)
def beacon_after_upstream_success_sensor(
    context: dg.RunStatusSensorContext,
) -> dg.RunRequest | dg.SkipReason:
    dagster_run = context.dagster_run
    if dagster_run.job_name not in UPSTREAM_JOB_NAMES:
        return dg.SkipReason("Ignoring non-upstream job success event.")

    orchestration_date = _orchestration_date_for_run(context.instance, dagster_run)
    if not orchestration_date:
        return dg.SkipReason("Could not determine an orchestration date for the upstream run.")

    missing_jobs: list[str] = []
    for job_name in sorted(UPSTREAM_JOB_NAMES):
        records = context.instance.get_run_records(
            filters=dg.RunsFilter(
                job_name=job_name,
                statuses=[dg.DagsterRunStatus.SUCCESS],
            ),
            limit=25,
        )
        matching_records = [
            record
            for record in records
            if _orchestration_date_for_run(context.instance, record.dagster_run)
            == orchestration_date
        ]
        if not matching_records:
            missing_jobs.append(job_name)

    if missing_jobs:
        return dg.SkipReason(
            "Waiting on successful upstream runs for "
            f"{orchestration_date}: {', '.join(missing_jobs)}"
        )

    return dg.RunRequest(
        run_key=f"beacon-executive-{orchestration_date}",
        tags={
            "orchestration_date": orchestration_date,
            "tenant": "beacon_hq",
            "triggered_by": "beacon_after_upstream_success_sensor",
        },
    )
