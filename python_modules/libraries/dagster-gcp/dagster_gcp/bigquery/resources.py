from typing import Generator, Optional

from dagster import resource
from dagster._config.structured_config import (
    ConfigurableResourceFactory,
    infer_schema_from_config_class,
)
from google.cloud import bigquery
from pydantic import Field

from .utils import setup_gcp_creds


class BigQueryResource(ConfigurableResourceFactory):
    project: Optional[str] = Field(
        default=None,
        description="""Project ID for the project which the client acts on behalf of. Will be passed
        when creating a dataset / job. If not passed, falls back to the default inferred from the
        environment.""",
    )

    location: Optional[str] = Field(
        default=None,
        description="Default location for jobs / datasets / tables.",
    )

    gcp_credentials: Optional[str] = Field(
        default=None,
        description=(
            "GCP authentication credentials. If provided, a temporary file will be created"
            " with the credentials and GOOGLE_APPLICATION_CREDENTIALS will be set to the"
            " temporary file. To avoid issues with newlines in the keys, you must base64"
            " encode the key. You can retrieve the base64 encoded key with this shell"
            " command: cat $GOOGLE_AUTH_CREDENTIALS | base64"
        ),
    )

    def create_resource(self, context) -> Generator:
        if self.gcp_credentials:
            with setup_gcp_creds(self.gcp_credentials):
                yield bigquery.Client(project=self.project, location=self.location)
        else:
            yield bigquery.Client(project=self.project, location=self.location)


@resource(
    config_schema=infer_schema_from_config_class(BigQueryResource),
    description="Dagster resource for connecting to BigQuery",
)
def bigquery_resource(context):
    return BigQueryResource.from_resource_context(context)
