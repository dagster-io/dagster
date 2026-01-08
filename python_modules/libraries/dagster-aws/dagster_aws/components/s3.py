from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import S3CredentialsComponent
from dagster_aws.s3.resources import S3FileManagerResource, S3Resource


@public
@preview
class S3ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3Resource for interacting with AWS S3."""

    credentials: S3CredentialsComponent = Field(description="Credentials for connecting to S3.")

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the S3 resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> S3Resource:
        """Resolves credentials and returns a configured S3 resource."""
        return S3Resource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


@public
@preview
class S3FileManagerResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3FileManagerResource for file management operations on AWS S3."""

    s3_bucket: str = Field(description="S3 bucket to use for the file manager.")
    s3_prefix: str = Field(
        default="dagster", description="Prefix to use for the S3 bucket for this file manager."
    )

    credentials: S3CredentialsComponent = Field(description="Credentials for connecting to S3.")

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the S3FileManager resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> S3FileManagerResource:
        """Resolves credentials and returns a configured S3FileManagerResource."""
        return S3FileManagerResource(
            s3_bucket=self.s3_bucket, s3_prefix=self.s3_prefix, **self.credentials.render_as_dict()
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


S3ResourceComponent.model_rebuild()

S3FileManagerResourceComponent.model_rebuild()
