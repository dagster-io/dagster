import dagster as dg


@dg.schedule(cron_schedule="0 0 * * *", target="*")
def tutorial_schedule(
    context: dg.ScheduleEvaluationContext,
) -> dg.RunRequest | dg.SkipReason:
    return dg.SkipReason(
        "Skipping. Change this to return a RunRequest to launch a run."
    )
