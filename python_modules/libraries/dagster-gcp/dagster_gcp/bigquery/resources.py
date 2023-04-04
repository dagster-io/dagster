from dagster import resource
from google.cloud import bigquery

from .configs import bq_resource_config
from .utils import setup_gcp_creds


@resource(
    config_schema=bq_resource_config(), description="Dagster resource for connecting to BigQuery"
)
def bigquery_resource(context):
    no_creds_config = {
        key: value for key, value in context.resource_config.items() if key != "gcp_credentials"
    }

    if context.resource_config.get("gcp_credentials"):
        with setup_gcp_creds(context):
            yield bigquery.Client(**no_creds_config)
    else:
        yield bigquery.Client(**no_creds_config)
