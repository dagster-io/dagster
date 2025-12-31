from functools import cached_property
from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_aws.components.credentials import RedshiftCredentialsComponent
from dagster_aws.redshift.resources import RedshiftClientResource


@public
@preview
class RedshiftClientResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a RedshiftClientResource for connecting to and querying Amazon Redshift."""

    credentials: Union[RedshiftCredentialsComponent, str] = Field(
        description="Redshift credentials - inline configuration or reference."
    )
    resource_key: Optional[str] = Field(
        default=None, description="The key under which the resource will be bound."
    )

    @cached_property
    def _resource(self) -> RedshiftClientResource:
        creds_data = (
            self.credentials.model_dump(exclude_none=True)
            if not isinstance(self.credentials, str)
            else {}
        )
        return RedshiftClientResource(**creds_data)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()
