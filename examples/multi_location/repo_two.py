from dagster import pipeline, repository, solid


@solid
def conflicting_solid(_):
    pass


@pipeline
def conflicting_pipeline():
    conflicting_solid()


@repository
def repo_two():
    return [conflicting_pipeline]
