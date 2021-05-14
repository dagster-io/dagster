from dagster import pipeline, repository, solid


@solid
def add_one(num: int) -> int:
    return num + 1


@solid
def add_two(num: int) -> int:
    return num + 2


@solid
def subtract(left: int, right: int) -> int:
    return left - right


@pipeline
def do_math():
    subtract(add_one(), add_two())


@repository
def my_repo():
    return [do_math]
