from functools import cached_property
from typing import Union

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
    resource_key: str = Field(
        default="redshift",
        description="The key under which the Redshift resource will be bound to the definitions.",
    )

    @cached_property
    def _resource(self) -> RedshiftClientResource:
        if isinstance(self.credentials, str):
            raise ValueError(
                "Redshift credentials cannot be a raw string template without connection details."
            )
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
