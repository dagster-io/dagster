from lakehouse import snowflake_table, SnowflakeLakehouse, construct_lakehouse_pipeline

from dagster_snowflake import snowflake_resource


@snowflake_table
def TableOne(_context):
    pass


def test_snowflake():
    construct_lakehouse_pipeline(
        name='snowflake_lake',
        lakehouse_tables=[TableOne],
        resources={'snowflake': snowflake_resource, 'lakehouse': SnowflakeLakehouse()},
    )
