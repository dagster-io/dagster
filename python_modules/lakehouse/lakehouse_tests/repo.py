from dagster import RepositoryDefinition
from test_typed_pyspark_lakehouse import typed_lakehouse_pipeline


def lakehouse_test_repo():
    return RepositoryDefinition(
        name='lakehouse_test_repo', pipeline_defs=[typed_lakehouse_pipeline]
    )
