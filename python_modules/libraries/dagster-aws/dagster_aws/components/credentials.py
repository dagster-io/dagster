from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field


@public
@preview
class Boto3CredentialsComponent(dg.Component, dg.Resolvable, dg.Model):
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
    """Configuration for S3-specific credentials, including unsigned session support."""

    use_unsigned_session: Optional[Union[bool, str]] = Field(
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
    polling_interval: Union[int, str] = Field(
        default=5,
        description=(
            "Time in seconds between checks to see if a query execution is finished. 5 seconds"
            " by default. Must be non-negative."
        ),
    )
    max_polls: Union[int, str] = Field(
        default=120,
        description=(
            "Number of times to poll before timing out. 120 attempts by default. When coupled"
            " with the default polling_interval, queries will timeout after 10 minutes (120 * 5"
            " seconds). Must be greater than 0."
        ),
    )
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID for authentication purposes."
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key for authentication purposes."
    )


@public
@preview
class RedshiftCredentialsComponent(dg.Component, dg.Resolvable, dg.Model):
    """Credentials and connection configuration for Redshift."""

    host: Optional[str] = Field(default=None, description="Redshift host")
    port: Union[int, str] = Field(default=5439, description="Redshift port")
    user: Optional[str] = Field(default=None, description="Username for Redshift connection")
    password: Optional[str] = Field(default=None, description="Password for Redshift connection")
    database: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default database to use. After login, you can use USE DATABASE to change"
            " the database."
        ),
    )
    autocommit: Optional[Union[bool, str]] = Field(
        default=None, description="Whether to autocommit queries"
    )
    connect_timeout: Union[int, str] = Field(
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
