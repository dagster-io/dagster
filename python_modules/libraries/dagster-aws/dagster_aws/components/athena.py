from functools import cached_property
from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.athena.resources import AthenaClientResource
from dagster_aws.components.credentials import AthenaCredentialsComponent


@public
@preview
class AthenaClientResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an AthenaClientResource for querying Amazon Athena."""

    credentials: Union[AthenaCredentialsComponent, str] = Field(
        description="Athena credentials - inline configuration or reference."
    )
    resource_key: Optional[str] = Field(
        default=None, description="The key under which the resource will be bound."
    )

    @cached_property
    def _resource(self) -> AthenaClientResource:
        creds_data = (
            self.credentials.model_dump(exclude_none=True)
            if not isinstance(self.credentials, str)
            else {}
        )
        return AthenaClientResource(**creds_data)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()
