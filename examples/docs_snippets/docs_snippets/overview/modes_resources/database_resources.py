from dagster import IntSource, StringSource, resource
from sqlalchemy import create_engine


@resource
def sqlite_database(_):
    class SQLiteDatabase:
        def execute_query(self, query):
            engine = create_engine("sqlite:///tmp.db")
            with engine.connect() as conn:
                conn.execute(query)

    return SQLiteDatabase()


@resource(
    config_schema={
        "hostname": StringSource,
        "port": IntSource,
        "username": StringSource,
        "password": StringSource,
        "db_name": StringSource,
    }
)
def postgres_database(init_context):
    class PostgresDatabase:
        def __init__(self, resource_config):
            self.hostname = resource_config["hostname"]
            self.port = resource_config["port"]
            self.username = resource_config["username"]
            self.password = resource_config["password"]
            self.db_name = resource_config["db_name"]

        def execute_query(self, query):
            engine = create_engine(
                f"postgresql://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.db_name}"
            )
            with engine.connect() as conn:
                conn.execute(query)

    return PostgresDatabase(init_context.resource_config)
