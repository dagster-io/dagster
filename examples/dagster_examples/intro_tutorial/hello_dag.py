from dagster import pipeline, solid


@solid
def solid_one(_):
    return 'foo'


@solid
def solid_two(_, arg_one):
    return arg_one * 2


@pipeline
def hello_dag_pipeline():
    return solid_two(solid_one())
