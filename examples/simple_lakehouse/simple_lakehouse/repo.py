from dagster import repository
from simple_lakehouse.pipelines import simple_lakehouse_pipeline


@repository
def simple_lakehouse():
    return [simple_lakehouse_pipeline]
