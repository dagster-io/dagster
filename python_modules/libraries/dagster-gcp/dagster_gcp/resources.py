import google.api_core.exceptions

from google.cloud import bigquery

from dagster import resource

from .configs import bq_resource_config
from .types import BigQueryError


class BigQueryClient:
    def __init__(self, project, location):
        self.project = project
        self.location = location

    @property
    def client(self):
        return bigquery.Client(project=self.project, location=self.location)

    def query(self, sql_query, job_config):
        return self.client.query(sql_query, job_config=job_config).to_dataframe()

    def create_dataset(self, dataset, exists_ok):
        try:
            self.client.create_dataset(dataset, exists_ok)
        except google.api_core.exceptions.Conflict:
            raise BigQueryError('Dataset "%s" already exists and exists_ok is false' % dataset)

    def delete_dataset(self, dataset, delete_contents, not_found_ok):
        try:
            self.client.delete_dataset(
                dataset=dataset, delete_contents=delete_contents, not_found_ok=not_found_ok
            )
        except google.api_core.exceptions.NotFound:
            raise BigQueryError('Dataset "%s" does not exist and not_found_ok is false' % dataset)


@resource(
    config_field=bq_resource_config(), description='Dagster resource for connecting to BigQuery'
)
def bigquery_resource(context):
    return BigQueryClient(
        context.resource_config.get('project'), context.resource_config.get('location')
    )
