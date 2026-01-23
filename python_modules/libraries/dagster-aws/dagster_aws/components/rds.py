from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.rds.resources import RDSResource


@public
@preview
class RDSResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an RDSResource for interacting with AWS RDS service."""

    credentials: Boto3CredentialsComponent = Field(
        description="AWS credentials - inline configuration."
    )
    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the RDS resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> RDSResource:
        """Resolves credentials and returns a configured RDS resource."""
        return RDSResource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
