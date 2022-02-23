from dagster.utils import file_relative_path

AIRBYTE_CONNECTION_ID = "15722450-ae59-4c65-a784-953808d7812c"
AIRBYTE_CONFIG = {"host": "localhost", "port": "8000"}
DBT_PROJECT_DIR = file_relative_path(__file__, "../mds_dbt")
DBT_PROFILES_DIR = file_relative_path(__file__, "../mds_dbt/config")
DBT_CONFIG = {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}
