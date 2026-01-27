from functools import cached_property
from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.ssm.resources import ParameterStoreResource, ParameterStoreTag, SSMResource


@public
@preview
class SSMResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a SSMResource for interacting with AWS Systems Manager."""

    credentials: Boto3CredentialsComponent = Field(
        description="AWS credentials - inline configuration."
    )
    resource_key: Optional[str] = Field(
        default=None, description="The key under which the resource will be bound in definitions."
    )

    @cached_property
    def resource(self) -> SSMResource:
        """Resolves credentials and returns a configured SSM resource."""
        return SSMResource(**self.credentials.render_as_dict())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


@public
@preview
class ParameterStoreResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a ParameterStoreResource for fetching parameters from AWS SSM Parameter Store."""

    credentials: Boto3CredentialsComponent = Field(
        description="AWS credentials - inline configuration."
    )

    parameters: list[str] = Field(
        default=[],
        description="AWS SSM Parameter store parameters with this tag will be fetched and made available.",
    )

    parameter_tags: list[ParameterStoreTag] = Field(
        default=[],
        description="AWS SSM Parameter store parameters with this tag will be fetched and made available.",
    )

    parameter_paths: list[str] = Field(
        default=[], description="List of path prefixes to pull parameters from."
    )
    with_decryption: bool = Field(
        default=False, description="Whether to decrypt secure string parameters."
    )

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the ParameterStore resource will be bound to the definitions.",
    )

    @cached_property
    def resource(self) -> ParameterStoreResource:
        return ParameterStoreResource(
            **self.credentials.render_as_dict(),
            parameters=self.parameters,
            parameter_paths=self.parameter_paths,
            parameter_tags=self.parameter_tags,
            with_decryption=self.with_decryption,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
