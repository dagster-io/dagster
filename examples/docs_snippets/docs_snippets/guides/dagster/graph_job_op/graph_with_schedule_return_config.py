from dagster import graph, op, schedule


@op(config_schema={"param": str})
def do_something(_):
    ...


@graph
def do_it_all():
    do_something()


@schedule(cron_schedule="0 0 * * *", job=do_it_all.to_job())
def do_it_all_schedule():
    return {"solids": {"do_something": {"config": {"param": "some_val"}}}}
