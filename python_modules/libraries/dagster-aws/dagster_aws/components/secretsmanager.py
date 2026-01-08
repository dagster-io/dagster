from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.secretsmanager.resources import (
    SecretsManagerResource,
    SecretsManagerSecretsResource,
)


@public
@preview
class SecretsManagerResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a SecretsManagerResource for interacting with AWS Secrets Manager."""

    credentials: Boto3CredentialsComponent = Field(
        description="AWS credentials - inline configuration."
    )
    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the SecretsManager resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> SecretsManagerResource:
        """Resolves credentials and returns a configured SecretsManager resource."""
        return SecretsManagerResource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


@public
@preview
class SecretsManagerSecretsResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a SecretsManagerSecretsResource for fetching secrets from AWS Secrets Manager."""

    credentials: Boto3CredentialsComponent = Field(
        description="AWS credentials - inline configuration."
    )
    secrets: list[str] = Field(
        default=[], description="An array of AWS Secrets Manager secrets ARNs to fetch."
    )
    secrets_tag: Optional[str] = Field(
        default=None,
        description="AWS Secrets Manager secrets with this tag will be fetched and made available.",
    )
    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the SecretsManagerSecrets resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> SecretsManagerSecretsResource:
        creds_data = self.credentials.render_as_dict()
        return SecretsManagerSecretsResource(
            **creds_data,
            secrets=self.secrets,
            secrets_tag=self.secrets_tag,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
