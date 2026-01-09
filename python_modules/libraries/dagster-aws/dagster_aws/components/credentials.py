from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import BaseModel, Field


class CredentialsRenderMixin:
    """A mixin to provide shared dictionary rendering logic for AWS credentials."""

    def render_as_dict(self) -> dict:
        """Returns the credentials as a dictionary, excluding None values."""
        assert isinstance(self, BaseModel)
        return self.model_dump(exclude_none=True)


@public
@preview
class Boto3CredentialsComponent(dg.Component, dg.Resolvable, dg.Model, CredentialsRenderMixin):
    """Configuration for standard AWS SDK (Boto3) credentials and session settings."""

    region_name: Optional[str] = Field(
        default=None, description="Specifies a custom region for the Boto3 session"
    )
    endpoint_url: Optional[str] = Field(
        default=None, description="Specifies a custom endpoint for the Boto3 session."
    )
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID to use when creating the boto3 session."
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key to use when creating the boto3 session."
    )
    aws_session_token: Optional[str] = Field(
        default=None, description="AWS session token to use when creating the boto3 session."
    )
    profile_name: Optional[str] = Field(
        default=None, description="Specifies a profile to connect that session"
    )
    use_ssl: bool = Field(
        default=True, description="Whether or not to use SSL. By default, SSL is used."
    )
    verify: Optional[bool] = Field(
        default=True,
        description="Whether or not to verify SSL certificates. By default SSL certificates are verified.",
    )
    max_attempts: int = Field(
        default=5,
        description=(
            "This provides Boto3's retry handler with a value of maximum retry attempts, where the"
            " initial call counts toward the max_attempts value that you provide"
        ),
    )
    retry_mode: Optional[str] = Field(
        default=None, description="Specifies the retry mode to use for the Boto3 session."
    )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


@public
@preview
class S3CredentialsComponent(Boto3CredentialsComponent):
    """Configuration for S3-specific credentials, including unsigned session support."""

    use_unsigned_session: Optional[bool] = Field(
        default=None, description="Specifies whether to use an unsigned S3 session."
    )


@public
@preview
class AthenaCredentialsComponent(Boto3CredentialsComponent):
    """Configuration for Athena-specific authentication and query settings."""

    workgroup: Optional[str] = Field(
        default="primary",
        description=(
            "The Athena WorkGroup to use."
            " https://docs.aws.amazon.com/athena/latest/ug/manage-queries-control-costs-with-workgroups.html"
        ),
    )
    polling_interval: int = Field(
        default=5,
        description=(
            "Time in seconds between checks to see if a query execution is finished. 5 seconds"
            " by default. Must be non-negative."
        ),
    )
    max_polls: int = Field(
        default=120,
        description=(
            "Number of times to poll before timing out. 120 attempts by default. When coupled"
            " with the default polling_interval, queries will timeout after 10 minutes (120 * 5"
            " seconds). Must be greater than 0."
        ),
    )
