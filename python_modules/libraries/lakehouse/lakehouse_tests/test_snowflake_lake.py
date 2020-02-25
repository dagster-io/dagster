from dagster_snowflake import snowflake_resource
from lakehouse import SnowflakeLakehouse, construct_lakehouse_pipeline, snowflake_table


@snowflake_table
def TableOne(_context):
    pass


def test_snowflake():
    construct_lakehouse_pipeline(
        name='snowflake_lake',
        lakehouse_tables=[TableOne],
        resources={'snowflake': snowflake_resource, 'lakehouse': SnowflakeLakehouse()},
    )
