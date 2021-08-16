from dagster import daily_partitioned_config, graph, op, repository, schedule_from_partitions


@op(config_schema={"date": str})
def do_something_with_config(context):
    return context.op_config["date"]


@graph
def do_it_all():
    do_something_with_config()


@daily_partitioned_config(start_date="2020-01-01")
def do_it_all_config(start, _end):
    return {"solids": {"do_something_with_config": {"config": {"date": str(start)}}}}


do_it_all_job = do_it_all.to_job(config=do_it_all_config)
do_it_all_schedule = schedule_from_partitions(do_it_all_job)


@repository
def do_it_all_repo():
    return [do_it_all_schedule]
