import os

from dagster import graph, op, repository, resource


@resource
def database_client():
    ...


def get_env():
    return os.getenv("DEPLOYMENT", "local")


# start_database_example
@op(required_resource_keys={"database"})
def get_one(context):
    context.resources.database.execute_query("SELECT 1")


@graph
def get_one_from_db():
    get_one()


@repository
def my_repo():
    resources_by_env = {
        "local": {
            "database": database_client.configured(
                {
                    "username": {"env": "DEV_USER"},
                    "password": {"env": "DEV_PASSWORD"},
                    "hostname": "localhost",
                    "db_name": "DEVELOPMENT",
                    "port": "5432",
                }
            )
        },
        "production": {
            "database": database_client.configured(
                {
                    "username": {"env": "SYSTEM_USER"},
                    "password": {"env": "SYSTEM_PASSWORD"},
                    "hostname": "abccompany",
                    "db_name": "PRODUCTION",
                    "port": "5432",
                }
            )
        },
    }
    return [get_one_from_db.to_job(resource_defs=resources_by_env[get_env()])]


# end_database_example
