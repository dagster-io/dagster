import google.api_core.exceptions
import six
from google.cloud import bigquery
from google.cloud.bigquery.client import _DEFAULT_NUM_RETRIES
from google.cloud.bigquery.retry import DEFAULT_RETRY

from dagster import check, resource

from .configs import bq_resource_config
from .types import BigQueryError, BigQueryLoadSource


class BigQueryClient(bigquery.Client):
    def __init__(self, project=None):
        check.opt_str_param(project, 'project')
        super(BigQueryClient, self).__init__(project=project)

    def create_dataset(self, dataset, exists_ok=False, retry=DEFAULT_RETRY):
        try:
            super(BigQueryClient, self).create_dataset(dataset, exists_ok, retry)
        except google.api_core.exceptions.Conflict:
            six.raise_from(
                BigQueryError('Dataset "%s" already exists and exists_ok is false' % dataset), None
            )

    def delete_dataset(
        self, dataset, delete_contents=False, retry=DEFAULT_RETRY, not_found_ok=False
    ):
        try:
            super(BigQueryClient, self).delete_dataset(
                dataset, delete_contents=delete_contents, retry=retry, not_found_ok=not_found_ok
            )
        except google.api_core.exceptions.NotFound:
            six.raise_from(
                BigQueryError('Dataset "%s" does not exist and not_found_ok is false' % dataset),
                None,
            )

    def load_table_from_dataframe(
        self,
        dataframe,
        destination,
        num_retries=_DEFAULT_NUM_RETRIES,
        job_id=None,
        job_id_prefix=None,
        location=None,
        project=None,
        job_config=None,
        parquet_compression="snappy",
    ):
        try:
            return super(BigQueryClient, self).load_table_from_dataframe(
                dataframe,
                destination,
                num_retries,
                job_id,
                job_id_prefix,
                location,
                project,
                job_config,
                parquet_compression,
            )
        except ImportError as e:
            six.raise_from(
                BigQueryError(
                    'loading data to BigQuery from pandas DataFrames requires either '
                    'pyarrow or fastparquet to be installed. %s' % str(e)
                ),
                None,
            )

    def load_table_from_filepath(self, file_path, destination, job_config):
        with open(file_path, 'rb') as file_obj:
            return super(BigQueryClient, self).load_table_from_file(
                file_obj, destination, job_config=job_config
            )

    def load_table_from_source(self, source, load_input, destination, job_config):
        # Load from DataFrame. See: https://bit.ly/2GDhVt1
        if source == BigQueryLoadSource.DataFrame:
            return self.load_table_from_dataframe(load_input, destination, job_config=job_config)

        # Load from file. See: https://cloud.google.com/bigquery/docs/loading-data-local
        elif source == BigQueryLoadSource.File:
            return self.load_table_from_filepath(load_input, destination, job_config=job_config)

        # Load from GCS. See: https://cloud.google.com/bigquery/docs/loading-data-cloud-storage
        elif source == BigQueryLoadSource.GCS:
            return self.load_table_from_uri(load_input, destination, job_config=job_config)


@resource(config=bq_resource_config(), description='Dagster resource for connecting to BigQuery')
def bigquery_resource(context):
    return BigQueryClient(context.resource_config.get('project'))
