import os

from dagster_dbt import create_dbt_run_solid, create_dbt_test_solid

from dagster import file_relative_path, pipeline

PROJECT_DIR = file_relative_path(__file__, 'jaffle_shop')
PROFILES_DIR = file_relative_path(__file__, 'profiles')

JAFFLE_EXE_ENV = 'JAFFLE_PIPELINE_VENV_PYTHON_PATH'

jaffle_solid = create_dbt_run_solid(
    PROJECT_DIR, profiles_dir=PROFILES_DIR, dbt_executable=os.getenv(JAFFLE_EXE_ENV)
)
jaffle_test_solid = create_dbt_test_solid(
    PROJECT_DIR, profiles_dir=PROFILES_DIR, dbt_executable=os.getenv(JAFFLE_EXE_ENV)
)


@pipeline(
    description='''
In order for this to work, you must have run dbt seed once against the a database
called jaffle_shop, which you must manually create.

Additionally this expects that the environment variable JAFFLE_PIPELINE_VENV_PYTHON_PATH
points to a valid dbt executable. This allows dbt to execute in its own virtual environment
separate from the orchestration environment
'''
)
def jaffle_pipeline():
    jaffle_test_solid(jaffle_solid())
