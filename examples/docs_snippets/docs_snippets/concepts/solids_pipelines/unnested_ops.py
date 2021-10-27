from dagster import job, op


@op
def return_fifty():
    return 50.0


@op
def add_thirty_two(number):
    return number + 32.0


@op
def multiply_by_one_point_eight(number):
    return number * 1.8


@op
def log_number(context, number):
    context.log.info(f"number: {number}")


@job
def all_together_unnested():
    log_number(add_thirty_two(multiply_by_one_point_eight(return_fifty())))
