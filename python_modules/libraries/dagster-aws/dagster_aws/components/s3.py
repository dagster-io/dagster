from functools import cached_property
from typing import TYPE_CHECKING, Optional

import dagster as dg
from dagster._annotations import preview, public

from dagster_aws.components.credentials import Boto3CredentialsComponent
from dagster_aws.s3.resources import S3Resource

if TYPE_CHECKING:

    class Boto3CredentialsComponent(dg.Model): ...


@public
@preview
class S3ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    credentials: Boto3CredentialsComponent
    resource_key: Optional[str] = None

    @cached_property
    def _resource(self) -> S3Resource:
        return S3Resource(**self.credentials.model_dump())

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key:
            return dg.Definitions(resources={self.resource_key: self._resource})
        return dg.Definitions()


S3ResourceComponent.model_rebuild()
