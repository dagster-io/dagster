from dagster import pipeline, schedule
from dagster.legacy import solid


@solid(config_schema={"date": str})
def do_something(_):
    ...


@pipeline
def do_it_all():
    do_something()


@schedule(
    cron_schedule="0 0 * * *",
    pipeline_name="do_it_all",
    execution_timezone="US/Central",
)
def do_it_all_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {"solids": {"do_something": {"config": {"date": date}}}}
