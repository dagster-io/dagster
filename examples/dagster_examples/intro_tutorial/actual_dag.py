from dagster import lambda_solid, pipeline


@lambda_solid
def return_one():
    return 1


@lambda_solid
def multiply_by_two(arg_a):
    return arg_a * 2


@lambda_solid
def multiply_by_three(arg_a):
    return arg_a * 3


@lambda_solid
def multiply(arg_b, arg_c):
    return arg_b * arg_c


@pipeline
def actual_dag_pipeline(_):
    one = return_one()
    multiply(multiply_by_two(one), multiply_by_three(one))


def define_actual_dag_pipeline():
    return actual_dag_pipeline
