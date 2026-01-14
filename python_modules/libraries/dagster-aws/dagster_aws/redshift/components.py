from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import BaseModel, Field

from dagster_aws.redshift.resources import RedshiftClientResource


class CredentialsRenderMixin:
    """A mixin to provide shared dictionary rendering logic for AWS credentials."""

    def render_as_dict(self) -> dict:
        """Returns the credentials as a dictionary, excluding None values."""
        assert isinstance(self, BaseModel)
        return self.model_dump(exclude_none=True)


@public
@preview
class RedshiftCredentialsComponent(dg.Component, dg.Resolvable, dg.Model, CredentialsRenderMixin):
    """Credentials and connection configuration for Redshift."""

    host: Optional[str] = Field(default=None, description="Redshift host")
    port: int = Field(default=5439, description="Redshift port")
    user: Optional[str] = Field(default=None, description="Username for Redshift connection")
    password: Optional[str] = Field(default=None, description="Password for Redshift connection")
    database: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default database to use. After login, you can use USE DATABASE to change"
            " the database."
        ),
    )
    autocommit: Optional[bool] = Field(default=None, description="Whether to autocommit queries")
    connect_timeout: int = Field(
        default=5, description="Timeout for connection to Redshift cluster. Defaults to 5 seconds."
    )
    sslmode: Optional[str] = Field(
        default="require",
        description=(
            "SSL mode to use. See the Redshift documentation for reference:"
            " https://docs.aws.amazon.com/redshift/latest/mgmt/connecting-ssl-support.html"
        ),
    )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


@public
@preview
class RedshiftClientResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a RedshiftClientResource for connecting to and querying Amazon Redshift."""

    credentials: RedshiftCredentialsComponent = Field(
        description="Redshift credentials - inline configuration."
    )
    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the Redshift resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> RedshiftClientResource:
        """Resolves credentials and returns a configured Redshift resource."""
        return RedshiftClientResource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
