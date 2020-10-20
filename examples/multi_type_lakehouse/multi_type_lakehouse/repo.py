from dagster import repository
from multi_type_lakehouse.pipelines import multi_type_lakehouse_pipeline


@repository
def multi_type_lakehouse():
    return [multi_type_lakehouse_pipeline]
