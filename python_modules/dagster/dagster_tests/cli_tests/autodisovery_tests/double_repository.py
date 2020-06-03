from dagster import repository


@repository
def repo_one():
    return []


@repository
def repo_two():
    return []
