from dagster import graph, repository


@graph
def basic():
    pass


@repository
def basic_repo():
    return [basic.to_job()]