import dagster as dg


@dg.repository
def repo_one():
    return []


@dg.repository
def repo_two():
    return []
