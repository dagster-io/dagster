from pathlib import Path

DAGSTER_DBT_TABLE_SCHEMA_MACRO_NAME = "dagster__log_columns_in_relation.sql"
DAGSTER_DBT_TABLE_SCHEMA_MACRO_PATH = (
    Path(__file__).joinpath("..").resolve().joinpath(DAGSTER_DBT_TABLE_SCHEMA_MACRO_NAME)
)
DAGSTER_DBT_TABLE_SCHEMA_MACRO_INVOCATION = r"{{ dagster__log_columns_in_relation() }}"
