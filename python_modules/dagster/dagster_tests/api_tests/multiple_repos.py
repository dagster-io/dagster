import dagster as dg


@dg.repository(name="repo_one")
def repo_one_symbol():
    return []


@dg.repository
def repo_two():
    return []
