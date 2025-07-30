from functools import cached_property
from typing import Annotated, Optional, cast

import dagster as dg
import pydantic
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession


class DatabricksSessionComponent(dg.Component, dg.Model, dg.Resolvable):
    """Component which provides a Databricks session which can be used to execute code in Databricks.

    Usage in Python:

    .. code-block:: python

        import dagster as dg
        from dagster_databricks import DatabricksSessionComponent

        databricks = (
            dg.ComponentTree.for_project(Path(__file__))
            .load_component_at_path("my_databricks_session", as_type=DatabricksSessionComponent)
            .session
        )
        databricks.sql("SELECT 1")

    """

    host: Annotated[
        Optional[str],
        pydantic.Field(
            description="The Databricks workspace URL (e.g., https://dbc-12345678-1234.cloud.databricks.com)."
        ),
    ] = None
    token: Annotated[
        Optional[str],
        pydantic.Field(description="The Databricks personal access token used to authenticate."),
    ] = None
    cluster_id: Annotated[
        Optional[str],
        pydantic.Field(
            description="The cluster identifier where the Databricks Connect queries should be executed."
        ),
    ] = None
    serverless: Annotated[
        bool,
        pydantic.Field(
            description="Whether to use serverless compute. When True, cluster_id is ignored."
        ),
    ] = False
    client_id: Annotated[
        Optional[str],
        pydantic.Field(description="OAuth client ID for machine-to-machine authentication."),
    ] = None
    client_secret: Annotated[
        Optional[str],
        pydantic.Field(description="OAuth client secret for machine-to-machine authentication."),
    ] = None
    user_agent: Annotated[
        Optional[str],
        pydantic.Field(
            description="A user agent string identifying the application using Databricks Connect."
        ),
    ] = None
    headers: Annotated[
        Optional[dict[str, str]],
        pydantic.Field(description="Headers to use while initializing Databricks Connect."),
    ] = None

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

    @cached_property
    def session(self) -> SparkSession:
        """Constructs a DatabricksSession matching the configuration set in this component."""
        builder = cast("DatabricksSession.Builder", DatabricksSession.builder)

        # Build remote connection parameters
        if (
            self.host
            or self.token
            or self.cluster_id
            or self.serverless
            or self.client_id
            or self.client_secret
            or self.user_agent
            or self.headers
        ):
            remote_kwargs = {}

            if self.host:
                remote_kwargs["host"] = self.host
            if self.token:
                remote_kwargs["token"] = self.token
            if self.cluster_id:
                remote_kwargs["cluster_id"] = self.cluster_id
            if self.serverless:
                remote_kwargs["serverless"] = self.serverless
            if self.client_id:
                remote_kwargs["client_id"] = self.client_id
            if self.client_secret:
                remote_kwargs["client_secret"] = self.client_secret
            if self.user_agent:
                remote_kwargs["user_agent"] = self.user_agent
            if self.headers:
                remote_kwargs["headers"] = self.headers

            builder = builder.remote(**remote_kwargs)

        return builder.getOrCreate()
