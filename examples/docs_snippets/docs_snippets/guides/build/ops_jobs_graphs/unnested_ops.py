import dagster as dg


@dg.op
def return_fifty():
    return 50.0


@dg.op
def add_thirty_two(number):
    return number + 32.0


@dg.op
def multiply_by_one_point_eight(number):
    return number * 1.8


@dg.op
def log_number(context: dg.OpExecutionContext, number):
    context.log.info(f"number: {number}")


@dg.job
def all_together_unnested():
    log_number(add_thirty_two(multiply_by_one_point_eight(return_fifty())))
