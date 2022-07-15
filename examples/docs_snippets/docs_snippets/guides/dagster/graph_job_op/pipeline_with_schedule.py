from dagster import ScheduleDefinition, repository
from dagster._legacy import pipeline, solid


@solid
def do_something():
    ...


@pipeline
def do_it_all():
    do_something()


do_it_all_schedule = ScheduleDefinition(cron_schedule="0 0 * * *", pipeline_name="do_it_all")


@repository
def do_it_all_repository():
    return [do_it_all, do_it_all_schedule]
