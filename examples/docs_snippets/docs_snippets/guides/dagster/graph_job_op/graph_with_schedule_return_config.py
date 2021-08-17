from dagster import graph, op, schedule


@op(config_schema={"date": str})
def do_something(_):
    ...


@graph
def do_it_all():
    do_something()


@schedule(cron_schedule="0 0 * * *", job=do_it_all.to_job(), execution_timezone="US/Central")
def do_it_all_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {"solids": {"do_something": {"config": {"date": date}}}}
