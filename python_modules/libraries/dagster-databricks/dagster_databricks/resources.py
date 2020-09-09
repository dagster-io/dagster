from dagster import Field, StringSource, resource

from .databricks import DatabricksClient


@resource(
    config_schema={
        "host": Field(
            StringSource,
            is_required=True,
            description="Databricks host, e.g. uksouth.azuredatabricks.com",
        ),
        "token": Field(StringSource, is_required=True, description="Databricks access token",),
    }
)
def databricks_client(init_context):
    return DatabricksClient(
        host=init_context.resource_config["host"], token=init_context.resource_config["token"]
    )
