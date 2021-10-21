from dagster import (
    build_schedule_from_partitioned_job,
    daily_partitioned_config,
    job,
    op,
    repository,
)


@op(config_schema={"date": str})
def do_something_with_config(context):
    return context.op_config["date"]


@daily_partitioned_config(start_date="2020-01-01")
def do_it_all_config(start, _end):
    return {"solids": {"do_something_with_config": {"config": {"date": str(start)}}}}


@job(config=do_it_all_config)
def do_it_all():
    do_something_with_config()


do_it_all_schedule = build_schedule_from_partitioned_job(do_it_all)


@repository
def do_it_all_repo():
    return [do_it_all_schedule]
