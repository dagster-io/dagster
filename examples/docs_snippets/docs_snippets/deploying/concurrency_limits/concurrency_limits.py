from dagster import asset, job, op, schedule

# start_marker_priority


@job(tags={"dagster/priority": "3"})
def important_job(): ...


@schedule(
    cron_schedule="* * * * *",
    job_name="important_job",
    execution_timezone="US/Central",
    tags={"dagster/priority": "-1"},
)
def less_important_schedule(_): ...


# end_marker_priority


# start_global_concurrency
@op(tags={"dagster/concurrency_key": "redshift"})
def my_redshift_op(): ...


@asset(op_tags={"dagster/concurrency_key": "redshift"})
def my_redshift_table(): ...


# end_global_concurrency


# start_global_concurrency_priority
@op(tags={"dagster/concurrency_key": "foo", "dagster/priority": "3"})
def my_op(): ...


@asset(op_tags={"dagster/concurrency_key": "foo", "dagster/priority": "3"})
def my_asset(): ...


# end_global_concurrency_priority
