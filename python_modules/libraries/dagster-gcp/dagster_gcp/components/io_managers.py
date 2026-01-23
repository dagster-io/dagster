from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_gcp.gcs.io_manager import GCSPickleIOManager
from dagster_gcp.gcs.resources import GCSResource


@public
@preview
class GCSPickleIOManagerComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a GCSPickleIOManager for storing assets in GCS."""

    gcs_bucket: str = Field(description="GCS bucket to store files.")

    gcs_prefix: str = Field(
        default="dagster",
        description="Prefix to add to all file paths.",
    )

    project: Optional[str] = Field(
        default=None,
        description="Project name",
    )

    resource_key: Optional[str] = Field(
        default="io_manager",
        description="The key under which the IO manager will be bound to the definitions.",
    )

    @property
    def resource(self) -> GCSPickleIOManager:
        gcs_resource = GCSResource(project=self.project)

        return GCSPickleIOManager(
            gcs=gcs_resource,
            gcs_bucket=self.gcs_bucket,
            gcs_prefix=self.gcs_prefix,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})


GCSPickleIOManagerComponent.model_rebuild()
