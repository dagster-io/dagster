import six


from google.cloud.bigquery.job import QueryJobConfig, LoadJobConfig
from google.cloud.bigquery.table import EncryptionConfiguration, TimePartitioning

from dagster_pandas import DataFrame

from dagster import (
    check,
    InputDefinition,
    List,
    OutputDefinition,
    Path,
    Result,
    SolidDefinition,
    Nothing,
)

from .configs import (
    define_bigquery_query_config,
    define_bigquery_create_dataset_config,
    define_bigquery_delete_dataset_config,
    define_bigquery_load_config,
)

from .types import BigQueryError, BigQueryLoadSource

INPUT_READY = 'input_ready_sentinel'


def _extract_query_job_config(cfg):
    destination_encryption_configuration = cfg.get('destination_encryption_configuration')
    time_partitioning = cfg.get('time_partitioning')

    fields = [
        'allow_large_results',
        'clustering_fields',
        'create_disposition',
        'default_dataset',
        'destination',
        'dry_run',
        'flatten_results',
        'maximum_billing_tier',
        'maximum_bytes_billed',
        'priority',
        'query_parameters',
        'schema_update_options',
        'use_legacy_sql',
        'use_query_cache',
        'write_disposition',
    ]
    kwargs = {k: cfg.get(k) for k in fields if cfg.get(k) is not None}

    if destination_encryption_configuration is not None:
        kwargs['destination_encryption_configuration'] = EncryptionConfiguration(
            kms_key_name=destination_encryption_configuration
        )

    if time_partitioning is not None:
        kwargs['time_partitioning'] = TimePartitioning(
            field=time_partitioning['field'],
            expiration_ms=time_partitioning['expiration_ms'],
            require_partition_filter=time_partitioning['require_partition_filter'],
        )
    return QueryJobConfig(**kwargs) if kwargs else None


def _extract_load_job_config(cfg):
    destination_encryption_configuration = cfg.get('destination_encryption_configuration')
    time_partitioning = cfg.get('time_partitioning')

    fields = [
        'allow_jagged_rows',
        'allow_quoted_newlines',
        'autodetect',
        'clustering_fields',
        'create_disposition',
        'destination_encryption_configuration',
        'destination_table_description',
        'destination_table_friendly_name',
        'encoding',
        'field_delimiter',
        'ignore_unknown_values',
        'max_bad_records',
        'null_marker',
        'quote_character',
        'schema_update_options',
        'skip_leading_rows',
        'source_format',
        'time_partitioning',
        'use_avro_logical_types',
        'write_disposition',
    ]
    kwargs = {k: cfg.get(k) for k in fields if cfg.get(k) is not None}

    if destination_encryption_configuration is not None:
        kwargs['destination_encryption_configuration'] = EncryptionConfiguration(
            kms_key_name=destination_encryption_configuration
        )

    if time_partitioning is not None:
        kwargs['time_partitioning'] = TimePartitioning(
            field=time_partitioning['field'],
            expiration_ms=time_partitioning['expiration_ms'],
            require_partition_filter=time_partitioning['require_partition_filter'],
        )
    return LoadJobConfig(**kwargs) if kwargs else None


class BigQuerySolidDefinition(SolidDefinition):
    """
    Executes BigQuery SQL queries.

    Expects a BQ client to be provisioned in resources as context.resources.bq.
    """

    def __init__(self, name, sql_queries, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)
        description = check.opt_str_param(description, 'description', 'BigQuery query')

        def _transform_fn(context, _):
            query_job_config = context.solid_config.get('query_job_config', {})

            # Retrieve results as pandas DataFrames
            results = []
            for sql_query in sql_queries:
                # We need to construct a new QueryJobConfig for each query.
                # See: https://bit.ly/2VjD6sl
                cfg = _extract_query_job_config(query_job_config)
                context.log.info(
                    'executing query %s with config: %s'
                    % (sql_query, cfg.to_api_repr() if cfg else '(no config provided)')
                )
                results.append(context.resources.bq.query(sql_query, job_config=cfg))

            yield Result(results)

        super(BigQuerySolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(List(DataFrame))],
            transform_fn=_transform_fn,
            config_field=define_bigquery_query_config(),
            metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
        )


class BigQueryLoadSolidDefinition(SolidDefinition):
    '''BigQuery Load.

    This solid encapsulates loading data into BigQuery from a pandas DataFrame or from GCS.

    Expects a BQ client to be provisioned in resources as context.resources.bq.
    '''

    def _configure_for_source(self, source):
        '''We support BigQuery loads from in-memory DataFrames, local files, and GCS URIs.
        '''

        # Load DataFrame. See: https://bit.ly/2GDhVt1
        if source == BigQueryLoadSource.DataFrame:
            inputs = [InputDefinition('df', DataFrame)]

            def _load(client, inputs, destination, cfg):
                try:
                    return client.load_table_from_dataframe(
                        inputs.get('df'), destination=destination, job_config=cfg
                    ).result()
                except ImportError as e:
                    six.raise_from(
                        BigQueryError(
                            'loading data to BigQuery from pandas DataFrames requires either '
                            'pyarrow or fastparquet to be installed. %s' % str(e)
                        ),
                        None,
                    )

            return (inputs, _load)

        # Load File. See: https://cloud.google.com/bigquery/docs/loading-data-local
        elif source == BigQueryLoadSource.File:
            inputs = [InputDefinition('file_path', Path)]

            def _load(client, inputs, destination, cfg):
                with open(inputs.get('file_path'), 'rb') as file_obj:
                    client.load_table_from_file(
                        file_obj, destination=destination, job_config=cfg
                    ).result()

            return (inputs, _load)

        # Load Gcs. See: https://cloud.google.com/bigquery/docs/loading-data-cloud-storage
        elif source == BigQueryLoadSource.Gcs:
            inputs = [InputDefinition('source_uris', List(Path))]

            def _load(client, inputs, destination, cfg):
                return client.load_table_from_uri(
                    inputs['source_uris'], destination, job_config=cfg
                ).result()

            return (inputs, _load)

        # Should not get here unless client specified incorrect source
        else:
            raise BigQueryError(
                'invalid source specification -- must be one of [%s]'
                % ','.join(
                    [BigQueryLoadSource.DataFrame, BigQueryLoadSource.File, BigQueryLoadSource.Gcs]
                )
            )

    def __init__(self, name, source, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(
            description, 'description', 'BigQuery load_table_from_dataframe'
        )
        inputs, _load = self._configure_for_source(source)

        def _transform_fn(context, inputs):
            destination = context.solid_config.get('destination')
            load_job_config = context.solid_config.get('load_job_config', {})
            cfg = _extract_load_job_config(load_job_config)
            yield Result(None)

            context.log.info(
                'executing BQ load with config: %s'
                % (cfg.to_api_repr() if cfg else '(no config provided)')
            )
            _load(context.resources.bq.client, inputs, destination, cfg)

        super(BigQueryLoadSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=inputs,
            outputs=[OutputDefinition(Nothing)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_load_config(),
        )


class BigQueryCreateDatasetSolidDefinition(SolidDefinition):
    '''BigQuery Create Dataset.

    This solid encapsulates creating a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bq.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(description, 'description', 'BigQuery create_dataset')

        def _transform_fn(context, _):
            (dataset, exists_ok) = [context.solid_config.get(k) for k in ('dataset', 'exists_ok')]
            context.log.info('executing BQ create_dataset for dataset %s' % (dataset))
            context.resources.bq.create_dataset(dataset, exists_ok)
            yield Result(None)

        super(BigQueryCreateDatasetSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(Nothing)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_create_dataset_config(),
        )


class BigQueryDeleteDatasetSolidDefinition(SolidDefinition):
    '''BigQuery Delete Dataset.

    This solid encapsulates deleting a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bq.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(description, 'description', 'BigQuery delete_dataset')

        def _transform_fn(context, _):
            (dataset, delete_contents, not_found_ok) = [
                context.solid_config.get(k) for k in ('dataset', 'delete_contents', 'not_found_ok')
            ]
            context.log.info('executing BQ delete_dataset for dataset %s' % dataset)
            context.resources.bq.delete_dataset(dataset, delete_contents, not_found_ok)
            yield Result(None)

        super(BigQueryDeleteDatasetSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(Nothing)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_delete_dataset_config(),
        )
