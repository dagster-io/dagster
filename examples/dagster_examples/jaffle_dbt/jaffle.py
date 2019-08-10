from dagster import file_relative_path, pipeline

from dagster_dbt import create_dbt_solid

jaffle_solid = create_dbt_solid(file_relative_path(__file__, 'jaffle_shop'))


@pipeline
def jaffle_pipeline():
    jaffle_solid()  # pylint: disable=no-value-for-parameter
