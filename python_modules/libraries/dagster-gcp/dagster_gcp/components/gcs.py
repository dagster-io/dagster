from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_gcp.gcs.resources import GCSFileManagerResource, GCSResource


@public
@preview
class GCSResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a GCSResource for interacting with Google Cloud Storage."""

    project: Optional[str] = Field(
        default=None,
        description="Project name",
    )

    gcp_credentials: Optional[str] = Field(
        default=None,
        description="GCP authentication credentials (base64).",
    )

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the GCS resource will be bound to the definitions.",
    )

    @property
    def resource(self) -> GCSResource:
        """Returns a configured GCSResource."""
        return GCSResource(
            project=self.project,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


@public
@preview
class GCSFileManagerResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a GCSFileManagerResource."""

    project: Optional[str] = Field(
        default=None,
        description="Project name",
    )

    gcs_bucket: str = Field(description="GCS bucket to store files.")

    gcs_prefix: str = Field(
        default="dagster",
        description="Prefix to add to all file paths.",
    )

    gcp_credentials: Optional[str] = Field(
        default=None,
        description="GCP authentication credentials (base64).",
    )

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the GCS FileManager resource will be bound to the definitions.",
    )

    @property
    def resource(self) -> GCSFileManagerResource:
        """Returns a configured GCSFileManagerResource."""
        return GCSFileManagerResource(
            project=self.project,
            gcs_bucket=self.gcs_bucket,
            gcs_prefix=self.gcs_prefix,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


GCSResourceComponent.model_rebuild()
GCSFileManagerResourceComponent.model_rebuild()
