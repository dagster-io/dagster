# start_database_example
import dagster as dg


@dg.resource(config_schema={"username": dg.StringSource, "password": dg.StringSource})
def database_client(context: dg.InitResourceContext):
    username = context.resource_config["username"]
    password = context.resource_config["password"]
    ...


@dg.op(required_resource_keys={"database"})
def get_one(context: dg.OpExecutionContext):
    context.resources.database.execute_query("SELECT 1")


@dg.job(
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
