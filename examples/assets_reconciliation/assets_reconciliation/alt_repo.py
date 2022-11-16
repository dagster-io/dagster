from dagster import asset
from dagster._core.definitions.decorators.repository_decorator import repository

@asset
def baz(context):
    return 100

@repository
def alt_repo():
    return [baz]
