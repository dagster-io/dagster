import google.api_core.exceptions

from google.cloud import bigquery
from google.cloud.bigquery.job import QueryJobConfig, LoadJobConfig
from google.cloud.bigquery.table import EncryptionConfiguration, TimePartitioning

import dagster_pandas as dagster_pd

from dagster import (
    check,
    Bool,
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

from .types import BigQueryError

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
    """

    def __init__(self, name, sql_queries, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)
        description = check.opt_str_param(description, 'description', 'BigQuery query')

        def _transform_fn(context, _):
            (project, location) = [context.solid_config.get(k) for k in ('project', 'location')]
            query_job_config = context.solid_config.get('query_job_config', {})

            client = bigquery.Client(project=project, location=location)

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

                result = client.query(sql_query, job_config=cfg).to_dataframe()
                results.append(result)

            yield Result(results)

        super(BigQuerySolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(List(dagster_pd.DataFrame))],
            transform_fn=_transform_fn,
            config_field=define_bigquery_query_config(),
            metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
        )


class BigQueryLoadFromDataFrameSolidDefinition(SolidDefinition):
    '''BigQuery Load.

    This solid encapsulates loading data into BigQuery from a pandas DataFrame.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(
            description, 'description', 'BigQuery load_table_from_dataframe'
        )

        def _transform_fn(context, inputs):
            (project, location, destination) = [
                context.solid_config.get(k) for k in ('project', 'location', 'destination')
            ]
            load_job_config = context.solid_config.get('load_job_config', {})
            cfg = _extract_load_job_config(load_job_config)

            client = bigquery.Client(project=project, location=location)
            context.log.info(
                'executing BQ load_table_from_dataframe with config: %s'
                % (cfg.to_api_repr() if cfg else '(no config provided)')
            )

            client.load_table_from_dataframe(
                inputs['df'], destination=destination, job_config=cfg
            ).result()

            yield Result(True)

        super(BigQueryLoadFromDataFrameSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition('df', dagster_pd.DataFrame)],
            outputs=[OutputDefinition(Bool)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_load_config(),
        )


class BigQueryLoadFromGCSSolidDefinition(SolidDefinition):
    '''BigQuery: Load data from GCS.

    This solid encapsulates loading data into BigQuery from a GCS URI.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(
            description, 'description', 'BigQuery load_table_from_uri'
        )

        def _transform_fn(context, inputs):
            (project, location, destination) = [
                context.solid_config.get(k) for k in ('project', 'location', 'destination')
            ]
            load_job_config = context.solid_config.get('load_job_config', {})
            cfg = _extract_load_job_config(load_job_config)

            client = bigquery.Client(project=project, location=location)
            context.log.info('executing BQ load_table_from_uri')

            client.load_table_from_uri(inputs['source_uris'], destination, job_config=cfg).result()
            yield Result(True)

        super(BigQueryLoadFromGCSSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition('source_uris', List(Path))],
            outputs=[OutputDefinition(Bool)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_load_config(),
        )


class BigQueryCreateDatasetSolidDefinition(SolidDefinition):
    '''BigQuery Create Dataset.

    This solid encapsulates creating a BigQuery dataset.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(description, 'description', 'BigQuery create_dataset')

        def _transform_fn(context, _):
            (project, location, dataset, exists_ok) = [
                context.solid_config.get(k) for k in ('project', 'location', 'dataset', 'exists_ok')
            ]

            client = bigquery.Client(project=project, location=location)
            context.log.info('executing BQ create_dataset for dataset %s' % (dataset))

            try:
                client.create_dataset(dataset, exists_ok)
            except google.api_core.exceptions.Conflict:
                raise BigQueryError('Dataset "%s" already exists and exists_ok is false' % dataset)

            yield Result(True)

        super(BigQueryCreateDatasetSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(Bool)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_create_dataset_config(),
        )


class BigQueryDeleteDatasetSolidDefinition(SolidDefinition):
    '''BigQuery Delete Dataset.

    This solid encapsulates deleting a BigQuery dataset.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(description, 'description', 'BigQuery delete_dataset')

        def _transform_fn(context, _):
            (project, location, dataset, delete_contents, not_found_ok) = [
                context.solid_config.get(k)
                for k in ('project', 'location', 'dataset', 'delete_contents', 'not_found_ok')
            ]

            client = bigquery.Client(project=project, location=location)
            context.log.info('executing BQ delete_dataset for dataset %s' % dataset)

            try:
                client.delete_dataset(
                    dataset=dataset, delete_contents=delete_contents, not_found_ok=not_found_ok
                )
            except google.api_core.exceptions.NotFound:
                raise BigQueryError(
                    'Dataset "%s" does not exist and not_found_ok is false' % dataset
                )
            yield Result(True)

        super(BigQueryDeleteDatasetSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(Bool)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_delete_dataset_config(),
        )
