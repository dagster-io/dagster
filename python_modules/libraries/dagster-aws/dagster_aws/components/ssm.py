from functools import cached_property
from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.ssm.resources import ParameterStoreResource, SSMResource


@public
@preview
class SSMResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an SSMResource for interacting with AWS Systems Manager."""

    credentials: Union[Boto3CredentialsComponent, str] = Field(
        description="AWS credentials - inline configuration or reference to a credentials component."
    )
    resource_key: Optional[str] = Field(
        default="ssm", description="The key under which the resource will be bound in Definitions."
    )

    @cached_property
    def _resource(self) -> SSMResource:
        creds_data = (
            self.credentials.model_dump(exclude_none=True)
            if not isinstance(self.credentials, str)
            else {}
        )
        return SSMResource(**creds_data)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()


@public
@preview
class ParameterStoreResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a ParameterStoreResource for fetching parameters from AWS SSM Parameter Store."""

    credentials: Union[Boto3CredentialsComponent, str] = Field(
        description="AWS credentials - inline configuration or reference to a credentials component."
    )
    parameters: Optional[list[str]] = Field(
        default=None, description="List of parameter names to fetch."
    )
    resource_key: Optional[str] = Field(
        default="parameter_store",
        description="The key under which the ParameterStore resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> ParameterStoreResource:
        creds_data = (
            self.credentials.model_dump(exclude_none=True)
            if not isinstance(self.credentials, str)
            else {}
        )
        return ParameterStoreResource(
            **creds_data,
            parameters=self.parameters or [],
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()
