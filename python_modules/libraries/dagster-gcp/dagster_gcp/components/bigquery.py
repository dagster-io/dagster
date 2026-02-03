from typing import Optional

import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_gcp.bigquery.resources import BigQueryResource


@public
@preview
class BigQueryResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a BigQueryResource for interacting with Google BigQuery."""

    project: Optional[str] = Field(
        default=None,
        description=(
            "Project ID for the project which the client acts on behalf of. Will be passed when"
            " creating a dataset / job. If not passed, falls back to the default inferred from the"
            " environment."
        ),
    )

    location: Optional[str] = Field(
        default=None,
        description="Default location for jobs / datasets / tables.",
    )

    gcp_credentials: Optional[str] = Field(
        default=None,
        description=(
            "GCP authentication credentials. If provided, a temporary file will be created"
            " with the credentials and ``GOOGLE_APPLICATION_CREDENTIALS`` will be set to the"
            " temporary file. To avoid issues with newlines in the keys, you must base64"
            " encode the key. You can retrieve the base64 encoded key with this shell"
            " command: ``cat $GOOGLE_AUTH_CREDENTIALS | base64``"
        ),
    )

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the BigQuery resource will be bound to the definitions.",
    )

    @property
    def resource(self) -> BigQueryResource:
        """Returns a configured BigQueryResource."""
        return BigQueryResource(
            project=self.project,
            location=self.location,
            gcp_credentials=self.gcp_credentials,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
