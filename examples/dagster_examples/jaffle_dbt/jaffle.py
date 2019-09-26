'''
'''
from dagster_dbt import create_dbt_solid, create_dbt_test_solid

from dagster import file_relative_path, pipeline

PROJECT_DIR = file_relative_path(__file__, 'jaffle_shop')
PROFILES_DIR = file_relative_path(__file__, 'profiles')

jaffle_solid = create_dbt_solid(PROJECT_DIR, profiles_dir=PROFILES_DIR)
jaffle_test_solid = create_dbt_test_solid(PROJECT_DIR, profiles_dir=PROFILES_DIR)


@pipeline
def jaffle_pipeline():
    jaffle_test_solid(jaffle_solid())
