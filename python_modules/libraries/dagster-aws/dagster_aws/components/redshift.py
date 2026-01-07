from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import RedshiftCredentialsComponent
from dagster_aws.redshift.resources import RedshiftClientResource


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
        return dg.Definitions(resources={self.resource_key or "redshift": self.resource})
