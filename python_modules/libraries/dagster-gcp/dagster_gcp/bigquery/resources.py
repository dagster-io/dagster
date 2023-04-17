<<<<<<< HEAD
from typing import Optional, Iterator
from contextlib import contextmanager
=======
from contextlib import contextmanager
from typing import Optional
>>>>>>> c19b0a3426 (working...)

from dagster import ConfigurableResource, resource
from google.cloud import bigquery
from pydantic import Field

from .utils import setup_gcp_creds


class BigQueryResource(ConfigurableResource):
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

    @contextmanager
    def get_client(self) -> Iterator[bigquery.Client]:
        if self.gcp_credentials:
            with setup_gcp_creds(self.gcp_credentials):
                yield
        else:
            yield

    def get_client(self) -> bigquery.Client:
        return bigquery.Client(project=self.project, location=self.location)


@resource(
    config_schema=BigQueryResource.to_config_schema(),
    description="Dagster resource for connecting to BigQuery",
)
def bigquery_resource(context):
    return BigQueryResource.from_resource_context(context).get_client()
