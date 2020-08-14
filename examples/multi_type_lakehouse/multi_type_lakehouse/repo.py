from multi_type_lakehouse.pipelines import multi_type_lakehouse_pipeline

from dagster import repository


@repository
def multi_type_lakehouse():
    return [multi_type_lakehouse_pipeline]
