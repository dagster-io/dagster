import google.api_core.exceptions

from google.cloud import bigquery
from google.cloud.bigquery.job import QueryJobConfig, LoadJobConfig
from google.cloud.bigquery.table import EncryptionConfiguration

import dagster_pandas as dagster_pd

from dagster import (
    check,
    Bool,
    InputDefinition,
    List,
    OutputDefinition,
    Result,
    SolidDefinition,
    Nothing,
)

from .configs import (
    define_bigquery_config,
    define_bigquery_create_dataset_config,
    define_bigquery_delete_dataset_config,
    define_bigquery_load_config,
)

from .types import BigQueryError

INPUT_READY = 'input_ready_sentinel'


def _extract_solid_base_config(solid_config):
    # Extract parameters from config
    (project, location, destination_encryption_configuration) = [
        solid_config.get(k) for k in ('project', 'location', 'destination_encryption_configuration')
    ]

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

    kwargs = {k: solid_config.get(k) for k in fields if solid_config.get(k) is not None}

    if destination_encryption_configuration is not None:
        kwargs['destination_encryption_configuration'] = EncryptionConfiguration(
            kms_key_name=destination_encryption_configuration
        )

    return project, location, kwargs


class BigQuerySolidDefinition(SolidDefinition):
    """
    Executes BigQuery SQL queries.
    """

    def __init__(self, name, sql_queries, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)
        description = check.opt_str_param(description, 'description', 'BigQuery query')

        def _transform_fn(context, _):
            project, location, kwargs = _extract_solid_base_config(context.solid_config)

            client = bigquery.Client(project=project, location=location)

            # Retrieve results as pandas DataFrames
            results = []
            for sql_query in sql_queries:
                # We need to construct a new QueryJobConfig for each query.
                # See: https://bit.ly/2VjD6sl
                cfg = QueryJobConfig(**kwargs) if kwargs else None
                context.log.info(
                    'executing query %s with config: %s'
                    % (sql_query, cfg.to_api_repr() if cfg else '(no config provided)')
                )
                result = client.query(sql_query, job_config=cfg).to_dataframe()
                results.append(result)

            context.log.info(str(results))
            yield Result(results)

        super(BigQuerySolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(INPUT_READY, Nothing)],
            outputs=[OutputDefinition(List(dagster_pd.DataFrame))],
            transform_fn=_transform_fn,
            config_field=define_bigquery_config(),
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
            project, location, kwargs = _extract_solid_base_config(context.solid_config)
            cfg = LoadJobConfig(**kwargs) if kwargs else None

            client = bigquery.Client(
                project=project, location=location, default_query_job_config=cfg
            )
            context.log.info(
                'executing BQ load_table_from_dataframe with config: %s'
                % (cfg.to_api_repr() if cfg else '(no config provided)')
            )
            client.load_table_from_dataframe(inputs['df'], kwargs['destination']).result()
            yield Result(True)

        super(BigQueryLoadFromDataFrameSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition('df', dagster_pd.DataFrame)],
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
            project, location, kwargs = _extract_solid_base_config(context.solid_config)
            dataset = context.solid_config.get('dataset')
            exists_ok = context.solid_config.get('exists_ok')

            cfg = QueryJobConfig(**kwargs) if kwargs else None
            client = bigquery.Client(
                project=project, location=location, default_query_job_config=cfg
            )
            context.log.info(
                'executing BQ create_dataset for dataset %s with config: %s'
                % (dataset, cfg.to_api_repr() if cfg else '(no config provided)')
            )
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
            project, location, kwargs = _extract_solid_base_config(context.solid_config)
            dataset = context.solid_config.get('dataset')
            delete_contents = context.solid_config.get('delete_contents')
            not_found_ok = context.solid_config.get('not_found_ok')

            cfg = QueryJobConfig(**kwargs) if kwargs else None
            client = bigquery.Client(
                project=project, location=location, default_query_job_config=cfg
            )
            context.log.info(
                'executing BQ delete_dataset for dataset %s with config: %s'
                % (dataset, cfg.to_api_repr() if cfg else '(no config provided)')
            )
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
