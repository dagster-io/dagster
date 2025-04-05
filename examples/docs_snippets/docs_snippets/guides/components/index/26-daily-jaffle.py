import dagster as dg


@dg.schedule(cron_schedule="@daily", target="*")
def daily_jaffle(context: dg.ScheduleEvaluationContext): ...
