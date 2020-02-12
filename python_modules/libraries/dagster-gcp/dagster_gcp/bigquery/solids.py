from dagster_pandas import DataFrame
from google.cloud.bigquery.job import LoadJobConfig, QueryJobConfig
from google.cloud.bigquery.table import EncryptionConfiguration, TimePartitioning

from dagster import InputDefinition, List, Nothing, OutputDefinition, Path, check, solid

from .configs import (
    define_bigquery_create_dataset_config,
    define_bigquery_delete_dataset_config,
    define_bigquery_load_config,
    define_bigquery_query_config,
)
from .types import BigQueryLoadSource

_START = 'start'


def _preprocess_config(cfg):
    destination_encryption_configuration = cfg.get('destination_encryption_configuration')
    time_partitioning = cfg.get('time_partitioning')

    if destination_encryption_configuration is not None:
        cfg['destination_encryption_configuration'] = EncryptionConfiguration(
            kms_key_name=destination_encryption_configuration
        )

    if time_partitioning is not None:
        cfg['time_partitioning'] = TimePartitioning(**time_partitioning)

    return cfg


def bq_solid_for_queries(sql_queries):
    """
    Executes BigQuery SQL queries.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    """

    sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)

    @solid(
        input_defs=[InputDefinition(_START, Nothing)],
        output_defs=[OutputDefinition(List[DataFrame])],
        config=define_bigquery_query_config(),
        required_resource_keys={'bigquery'},
        tags={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
    )
    def bq_solid(context):  # pylint: disable=unused-argument
        query_job_config = _preprocess_config(context.solid_config.get('query_job_config', {}))

        # Retrieve results as pandas DataFrames
        results = []
        for sql_query in sql_queries:
            # We need to construct a new QueryJobConfig for each query.
            # See: https://bit.ly/2VjD6sl
            cfg = QueryJobConfig(**query_job_config) if query_job_config else None
            context.log.info(
                'executing query %s with config: %s'
                % (sql_query, cfg.to_api_repr() if cfg else '(no config provided)')
            )
            results.append(
                context.resources.bigquery.query(sql_query, job_config=cfg).to_dataframe()
            )

        return results

    return bq_solid


BIGQUERY_LOAD_CONFIG = define_bigquery_load_config()


@solid(
    input_defs=[InputDefinition('paths', List[Path])],
    output_defs=[OutputDefinition(Nothing)],
    config=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={'bigquery'},
)
def import_gcs_paths_to_bq(context, paths):
    return _execute_load_in_source(context, paths, BigQueryLoadSource.GCS)


@solid(
    input_defs=[InputDefinition('df', DataFrame)],
    output_defs=[OutputDefinition(Nothing)],
    config=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={'bigquery'},
)
def import_df_to_bq(context, df):
    return _execute_load_in_source(context, df, BigQueryLoadSource.DataFrame)


@solid(
    input_defs=[InputDefinition('path', Path)],
    output_defs=[OutputDefinition(Nothing)],
    config=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={'bigquery'},
)
def import_file_to_bq(context, path):
    return _execute_load_in_source(context, path, BigQueryLoadSource.File)


def _execute_load_in_source(context, source, source_name):
    destination = context.solid_config.get('destination')
    load_job_config = _preprocess_config(context.solid_config.get('load_job_config', {}))
    cfg = LoadJobConfig(**load_job_config) if load_job_config else None

    context.log.info(
        'executing BQ load with config: %s for source %s'
        % (cfg.to_api_repr() if cfg else '(no config provided)', source)
    )

    context.resources.bigquery.load_table_from_source(
        source_name, source, destination, job_config=cfg
    ).result()


@solid(
    input_defs=[InputDefinition(_START, Nothing)],
    config=define_bigquery_create_dataset_config(),
    required_resource_keys={'bigquery'},
)
def bq_create_dataset(context):
    '''BigQuery Create Dataset.

    This solid encapsulates creating a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    '''
    (dataset, exists_ok) = [context.solid_config.get(k) for k in ('dataset', 'exists_ok')]
    context.log.info('executing BQ create_dataset for dataset %s' % (dataset))
    context.resources.bigquery.create_dataset(dataset, exists_ok)


@solid(
    input_defs=[InputDefinition(_START, Nothing)],
    config=define_bigquery_delete_dataset_config(),
    required_resource_keys={'bigquery'},
)
def bq_delete_dataset(context):
    '''BigQuery Delete Dataset.

    This solid encapsulates deleting a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    '''

    (dataset, delete_contents, not_found_ok) = [
        context.solid_config.get(k) for k in ('dataset', 'delete_contents', 'not_found_ok')
    ]

    context.log.info('executing BQ delete_dataset for dataset %s' % dataset)

    context.resources.bigquery.delete_dataset(
        dataset, delete_contents=delete_contents, not_found_ok=not_found_ok
    )
