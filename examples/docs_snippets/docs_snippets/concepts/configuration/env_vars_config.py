# pylint: disable=unused-variable, unnecessary-ellipsis

# start_database_example
from dagster import StringSource, job, op, resource


@resource(config_schema={"username": StringSource, "password": StringSource})
def database_client(context):
    username = context.resource_config["username"]
    password = context.resource_config["password"]
    ...


@op(required_resource_keys={"database"})
def get_one(context):
    context.resources.database.execute_query("SELECT 1")


@job(
    resource_defs={
        "database": database_client.configured(
            {
                "username": {"env": "SYSTEM_USER"},
                "password": {"env": "SYSTEM_PASSWORD"},
            }
        )
    }
)
def get_one_from_db():
    get_one()


# end_database_example
