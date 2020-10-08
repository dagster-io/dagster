from dagster import lambda_solid, pipeline, repository


@lambda_solid
def do_something():
    return 1


@pipeline(name="extra")
def extra_pipeline():
    do_something()


@repository
def extra():
    return {
        "pipelines": {"extra": extra_pipeline},
    }
