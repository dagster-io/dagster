from dagster import lambda_solid, pipeline


@lambda_solid
def solid_one():
    return 'foo'


@lambda_solid
def solid_two(arg_one):
    return arg_one * 2


@pipeline
def hello_dag_pipeline():
    return solid_two(solid_one())
