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
                results.append(context.resources.bq.query(sql_query, job_config=cfg).to_dataframe())

            yield Result(results)

        super(BigQuerySolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(_START, Nothing)],
            outputs=[OutputDefinition(List(DataFrame))],
            transform_fn=_transform_fn,
            config_field=define_bigquery_query_config(),
            metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
        )


class BigQueryLoadSolidDefinition(SolidDefinition):
    '''BigQuery Load.

    This solid encapsulates loading data into BigQuery from a pandas DataFrame, local file, or GCS.

    Expects a BQ client to be provisioned in resources as context.resources.bq.
    '''

    def _inputs_for_source(self, source):
        if source == BigQueryLoadSource.DataFrame:
            return [InputDefinition('df', DataFrame)]
        elif source == BigQueryLoadSource.File:
            return [InputDefinition('file_path', Path)]
        elif source == BigQueryLoadSource.Gcs:
            return [InputDefinition('source_uris', List(Path))]
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

        def _transform_fn(context, inputs):
            destination = context.solid_config.get('destination')
            load_job_config = _preprocess_config(context.solid_config.get('load_job_config', {}))
            cfg = LoadJobConfig(**load_job_config) if load_job_config else None

            context.log.info(
                'executing BQ load with config: %s'
                % (cfg.to_api_repr() if cfg else '(no config provided)')
            )

            context.resources.bq.load_table_from_source(
                source, inputs, destination, job_config=cfg
            ).result()

            yield Result(None)

        super(BigQueryLoadSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=self._inputs_for_source(source),
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
            inputs=[InputDefinition(_START, Nothing)],
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

            context.resources.bq.delete_dataset(
                dataset, delete_contents=delete_contents, not_found_ok=not_found_ok
            )
            yield Result(None)

        super(BigQueryDeleteDatasetSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(_START, Nothing)],
            outputs=[OutputDefinition(Nothing)],
            transform_fn=_transform_fn,
            config_field=define_bigquery_delete_dataset_config(),
        )
