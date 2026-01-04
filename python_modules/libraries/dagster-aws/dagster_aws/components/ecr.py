from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.ecr import ECRPublicResource


@public
@preview
class ECRPublicResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an ECRPublicResource for connecting to AWS Public ECR."""

    credentials: Optional[Boto3CredentialsComponent] = Field(
        default=None,
        description="Optional AWS credentials. If not provided, environment defaults will be used.",
    )

    resource_key: str = Field(
        default="ecr_public",
        description="The key under which the ECR Public resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> ECRPublicResource:
        if self.credentials:
            return ECRPublicResource(**self.credentials.render_as_dict())
        return ECRPublicResource()

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()
