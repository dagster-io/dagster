from dagster import ScheduleDefinition, pipeline, solid


@solid
def do_something():
    ...


@pipeline
def do_it_all():
    do_something()


do_it_all_schedule = ScheduleDefinition(cron_schedule="0 0 * * *", pipeline_name="do_it_all")
