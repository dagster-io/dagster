# pylint: disable=unused-variable, unnecessary-ellipsis

# start_database_example
from dagster import StringSource, job, op, resource
from dagster._config.field_utils import EnvVar
from dagster._config.structured_config import Resource


class DatabaseClient(Resource):
    username: str
    password: str

    def execute_query(self, query):
        ...


@op
def get_one(database: DatabaseClient):
    database.execute_query("SELECT 1")


@job(
    resource_defs={
        "database": DatabaseClient(
            username=EnvVar("DATABASE_USERNAME"),
            password=EnvVar("DATABASE_PASSWORD"),
        )
    }
)
def get_one_from_db():
    get_one()


# end_database_example
