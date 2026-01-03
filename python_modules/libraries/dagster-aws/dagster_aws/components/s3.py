from functools import cached_property

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import S3CredentialsComponent
from dagster_aws.s3.resources import S3Resource


@public
@preview
class S3ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3Resource for interacting with Amazon S3."""

    credentials: S3CredentialsComponent = Field(description="Credentials for connecting to S3.")

    resource_key: str = Field(
        default="s3",
        description="The key under which the S3 resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> S3Resource:
        """Resolves credentials and returns a configured S3 resource."""
        return S3Resource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()


S3ResourceComponent.model_rebuild()
