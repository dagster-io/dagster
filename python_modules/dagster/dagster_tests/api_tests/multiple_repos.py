from dagster import In, Out, op, repository


@repository(name="repo_one")
def repo_one_symbol():
    return []


@repository
def repo_two():
    return []
