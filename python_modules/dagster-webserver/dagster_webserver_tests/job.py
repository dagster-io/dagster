from dagster import In, Int, Out, job, op, repository, schedule


@op(ins={"num": In(Int)}, out=Out(Int))
def add_one(num):
    return num + 1


@op(ins={"num": In(int)}, out=Out(int))
def mult_two(num):
    return num * 2


@job
def math():
    mult_two(num=add_one())


@schedule(
    cron_schedule="@daily",
    job_name="math",
)
def my_schedule(_):
    return {"ops": {"mult_two": {"inputs": {"num": {"value": 2}}}}}


@repository
def test_repository():
    return [math]
