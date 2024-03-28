# ruff: noqa

from dagster import job, op, DefaultScheduleStatus, Definitions, ScheduleDefinition


# start_op_job
@op
def count_orders():
    return 5


@op
def count_users(arg):
    return arg + 1


@job
def ecommerce_job():
    count_users(count_orders())


# end_op_job

# start_schedule
ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_job,
    cron_schedule="15 5 * * 1-5",
    default_status=DefaultScheduleStatus.RUNNING,
)


# end_schedule

# start_definitions
defs = Definitions(
    jobs=[ecommerce_job],
    schedules=[ecommerce_schedule],
)

# end_definitions
