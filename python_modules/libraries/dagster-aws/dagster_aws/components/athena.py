from functools import cached_property

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.athena.resources import AthenaClientResource
from dagster_aws.components.credentials import AthenaCredentialsComponent


@public
@preview
class AthenaClientResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an AthenaClientResource for executing queries against Amazon Athena."""

    credentials: AthenaCredentialsComponent = Field(
        description="Credentials for connecting to Athena."
    )

    resource_key: str = Field(
        default="athena",
        description="The key under which the Athena resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> AthenaClientResource:
        """Resolves credentials and returns a configured Athena resource."""
        return AthenaClientResource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        """Binds the Athena resource to the specified resource key in the definitions."""
        return dg.Definitions(resources={self.resource_key: self._resource})
