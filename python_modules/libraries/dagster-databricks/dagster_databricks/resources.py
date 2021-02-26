from dagster import Field, StringSource, resource

from .databricks import DatabricksClient


@resource(
    config_schema={
        "host": Field(
            StringSource,
            is_required=True,
            description="Databricks host, e.g. uksouth.azuredatabricks.com",
        ),
        "token": Field(
            StringSource,
            is_required=True,
            description="Databricks access token",
        ),
        "workspace_id": Field(
            StringSource,
            description="The Databricks workspace ID, as described in"
            "https://docs.databricks.com/workspace/workspace-details.html#workspace-instance-names-urls-and-ids."
            "This is used to log a URL for accessing the job in the Databricks UI.",
            is_required=False,
        ),
    }
)
def databricks_client(init_context):
    return DatabricksClient(
        host=init_context.resource_config["host"],
        token=init_context.resource_config["token"],
        workspace_id=init_context.resource_config.get("workspace_id"),
    )
