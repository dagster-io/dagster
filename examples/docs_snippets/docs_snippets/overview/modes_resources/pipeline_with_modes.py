from dagster import ModeDefinition, pipeline

from .database_resources import postgres_database, sqlite_database
from .solids_with_resources import generate_table_1, generate_table_2


@pipeline(
    mode_defs=[
        ModeDefinition("local_dev", resource_defs={"database": sqlite_database}),
        ModeDefinition("prod", resource_defs={"database": postgres_database}),
    ],
)
def generate_tables_pipeline():
    generate_table_1()
    generate_table_2()
