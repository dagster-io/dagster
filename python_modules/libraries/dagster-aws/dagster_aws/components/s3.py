from functools import cached_property

import boto3
import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import S3CredentialsComponent
from dagster_aws.s3 import S3FileManager, S3Resource


@public
@preview
class S3ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3Resource for interacting with AWS S3."""

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


@public
@preview
class S3FileManagerComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3FileManager for managing files on AWS S3."""

    credentials: S3CredentialsComponent = Field(description="Credentials for connecting to S3.")

    s3_bucket: str = Field(description="S3 bucket name to use for file storage.")

    s3_prefix: str = Field(default="", description="S3 prefix (folder) to use for file storage.")

    resource_key: str = Field(
        default="s3_file_manager",
        description="The key under which the S3FileManager resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> S3FileManager:
        """Constructs the S3FileManager using a boto3 session."""
        creds = self.credentials.render_as_dict()

        session_kwargs = {
            k: v
            for k, v in creds.items()
            if k
            in [
                "region_name",
                "profile_name",
                "aws_access_key_id",
                "aws_secret_access_key",
                "aws_session_token",
            ]
        }

        session = boto3.session.Session(**session_kwargs)

        return S3FileManager(
            s3_session=session,
            s3_bucket=self.s3_bucket,
            s3_base_key=self.s3_prefix,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()


S3ResourceComponent.model_rebuild()

S3FileManagerComponent.model_rebuild()
