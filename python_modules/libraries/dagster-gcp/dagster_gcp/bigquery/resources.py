import base64
import json
import os
import tempfile

from dagster import resource
from dagster._core.errors import DagsterInvalidDefinitionError
from google.cloud import bigquery

from .configs import bq_resource_config


@resource(
    config_schema=bq_resource_config(), description="Dagster resource for connecting to BigQuery"
)
def bigquery_resource(context):
    no_creds_config = {
        key: value for key, value in context.resource_config.items() if key != "gcp_credentials"
    }
    bq = bigquery.Client(**no_creds_config)

    if context.resource_config.get("gcp_credentials"):
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None:
            raise DagsterInvalidDefinitionError(
                "Resource config error: gcp_credentials config for BigQuery resource cannot"
                " be used if GOOGLE_APPLICATION_CREDENTIALS environment variable is set."
            )
        with tempfile.NamedTemporaryFile("w+") as f:
            temp_file_name = f.name
            json.dump(
                json.loads(base64.b64decode(context.resource_config.get("gcp_credentials"))),
                f,
            )
            f.flush()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_name
            try:
                yield bq
            finally:
                os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    else:
        yield bq
