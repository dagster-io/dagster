from dagster._utils import file_relative_path
from dagster_postgres.utils import get_conn_string

# =========================================================================
# To get this value, run `python -m assets_modern_data_stack.setup_airbyte`
# and grab the connection id that it prints at the end
AIRBYTE_CONNECTION_ID = "your_airbyte_connection_id"
# =========================================================================


PG_SOURCE_CONFIG = {
    "username": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
}
PG_DESTINATION_CONFIG = {
    "username": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
    "database": "postgres_replica",
}

AIRBYTE_CONFIG = {"host": "localhost", "port": "8000"}
DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_CONFIG = {"project_dir": DBT_PROJECT_DIR}
POSTGRES_CONFIG = {
    "con_string": get_conn_string(
        username=PG_DESTINATION_CONFIG["username"],
        password=PG_DESTINATION_CONFIG["password"],
        hostname=PG_DESTINATION_CONFIG["host"],
        port=str(PG_DESTINATION_CONFIG["port"]),
        db_name=PG_DESTINATION_CONFIG["database"],
    )
}
