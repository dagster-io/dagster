from dagster import pipeline, lambda_solid


@lambda_solid
def solid_one():
    return 'foo'


@lambda_solid
def solid_two(arg_one):
    return arg_one * 2


@pipeline
def hello_dag_pipeline(_):
    return solid_two(solid_one())


def define_hello_dag_pipeline():
    return hello_dag_pipeline
