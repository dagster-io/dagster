from dagster import repository

from .pipelines import dbt_example_pipeline


@repository
def dbt_example_repo():
    return [dbt_example_pipeline]
