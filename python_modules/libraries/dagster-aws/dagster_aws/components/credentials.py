from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field


@public
@preview
class Boto3CredentialsComponent(dg.Component, dg.Resolvable, dg.Model):
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
    use_ssl: Union[bool, str] = Field(
        default=True, description="Whether or not to use SSL. By default, SSL is used."
    )
    verify: Optional[Union[bool, str]] = Field(
        default=True,
        description="Whether or not to verify SSL certificates. By default SSL certificates are verified.",
    )
    max_attempts: Union[int, str] = Field(
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
    use_unsigned_session: Optional[Union[bool, str]] = Field(
        default=None, description="Specifies whether to use an unsigned S3 session."
    )
