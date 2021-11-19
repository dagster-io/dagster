from dagster import ScheduleDefinition, job, op


@op(config_schema={"param": str})
def do_something(_):
    ...


config = {"solids": {"do_something": {"config": {"param": "some_val"}}}}


@job(config=config)
def do_it_all():
    do_something()


do_it_all_schedule = ScheduleDefinition(job=do_it_all, cron_schedule="0 0 * * *")
