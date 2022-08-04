from dagster import job, repository


@job
def pipeline_one():
    pass


@job
def pipeline_two():
    pass


@repository
def multi_pipeline():
    return [pipeline_one, pipeline_two]
