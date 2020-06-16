from dagster import pipeline, repository, solid


@solid
def unique_solid(_):
    pass


@solid
def conflicting_solid(_):
    pass


@pipeline
def unique_pipeline():
    unique_solid()


@pipeline
def conflicting_pipeline():
    conflicting_solid()


@repository
def repo_one():
    return [unique_pipeline, conflicting_pipeline]
