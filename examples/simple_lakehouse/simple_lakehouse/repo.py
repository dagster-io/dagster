from simple_lakehouse.pipelines import simple_lakehouse_pipeline

from dagster import repository


@repository
def simple_lakehouse():
    return [simple_lakehouse_pipeline]
