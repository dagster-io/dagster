RESULTS = [1, 1, 0.4]


def some_random_result():
    return RESULTS.pop()


# isort: split
# start_random_job
from dagster import in_process_executor, job, op


@op
def start():
    return 1


@op
def unreliable(num: int) -> int:
    failure_rate = 0.5
    if some_random_result() < failure_rate:
        raise Exception("blah")

    return num


@op
def end(_num: int):
    pass


@job(executor_def=in_process_executor)
def unreliable_job():
    end(unreliable(start()))


# end_random_job
