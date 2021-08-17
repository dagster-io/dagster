from dagster import pipeline, schedule, solid


@solid(config_schema={"param": str})
def do_something(_):
    ...


@pipeline
def do_it_all():
    do_something()


@schedule(cron_schedule="0 0 * * *", pipeline_name="do_it_all")
def do_it_all_schedule():
    return {"solids": {"do_something": {"config": {"param": "some_val"}}}}
