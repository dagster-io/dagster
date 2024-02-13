from dagster import ScheduleDefinition, job, op, repository


@op
def add_one(num: int) -> int:
    return num + 1


@op
def mult_two(num: int) -> int:
    return num * 2


@job
def math():
    mult_two(add_one())


@op(config_schema={"gimme": str})
def needs_config(context):
    return context.op_config["gimme"]


@op
def no_config():
    return "ok"


@job
def subset_test():
    no_config()
    needs_config()


def define_schedules():
    math_hourly_schedule = ScheduleDefinition(
        name="math_hourly_schedule",
        cron_schedule="0 0 * * *",
        job_name="math",
        run_config={"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
    )

    return [math_hourly_schedule]


@repository
def test():
    return [math, subset_test] + define_schedules()
