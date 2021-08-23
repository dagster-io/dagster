from dagster import ScheduleDefinition, graph, op


@op
def do_something():
    ...


@graph
def do_it_all():
    do_something()


do_it_all_schedule = ScheduleDefinition(cron_schedule="0 0 * * *", job=do_it_all)
