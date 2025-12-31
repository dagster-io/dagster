from functools import cached_property
from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview, public

from dagster_aws.components.credentials import S3CredentialsComponent
from dagster_aws.s3.resources import S3Resource


@public
@preview
class S3ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides an S3Resource for interacting with Amazon S3."""

    credentials: Union[S3CredentialsComponent, str]
    resource_key: Optional[str] = None

    @cached_property
    def _resource(self) -> S3Resource:
        if isinstance(self.credentials, str):
            return S3Resource()

        creds_data = self.credentials.model_dump(exclude_none=True)
        return S3Resource(**creds_data)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()


S3ResourceComponent.model_rebuild()
