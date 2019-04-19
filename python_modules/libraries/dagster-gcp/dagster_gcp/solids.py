from google.cloud import bigquery
from google.cloud.bigquery.job import (
    CreateDisposition,
    SchemaUpdateOption,
    QueryJobConfig,
    QueryPriority,
    WriteDisposition,
)
from google.cloud.bigquery.table import EncryptionConfiguration

import dagster_pandas as dagster_pd

from dagster import check, InputDefinition, List, OutputDefinition, Result, SolidDefinition, Nothing
from .configs import define_bigquery_config


class BigQuerySolidDefinition(SolidDefinition):
    """
    Executes BigQuery SQL queries.
    """

    INPUT_READY = 'input_ready_sentinel'

    def __init__(self, name, sql_queries, description=None):
        name = check.str_param(name, 'name')
        sql_queries = check.list_param(sql_queries, 'sql queries', of_type=str)

        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a BigQuery query.',
        )

        def _transform_fn(context, _):
            # Extract parameters from config
            (project, location, destination_encryption_configuration) = [
                context.solid_config.get(k)
                for k in ('project', 'location', 'destination_encryption_configuration')
            ]

            kwargs = {}
            for k in [
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
            ]:
                if context.solid_config.get(k) is not None:
                    kwargs[k] = context.solid_config.get(k)

            if destination_encryption_configuration is not None:
                kwargs['destination_encryption_configuration'] = EncryptionConfiguration(
                    kms_key_name=destination_encryption_configuration
                )

            client = bigquery.Client(project=project, location=location)

            # Retrieve results as pandas DataFrames
            results = []
            for sql_query in sql_queries:
                # We need to construct a new QueryJobConfig for each query.
                # See: https://bit.ly/2VjD6sl
                cfg = QueryJobConfig(**kwargs) if len(kwargs) > 0 else None
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
            inputs=[InputDefinition(BigQuerySolidDefinition.INPUT_READY, Nothing)],
            outputs=[OutputDefinition(List(dagster_pd.DataFrame))],
            transform_fn=_transform_fn,
            config_field=define_bigquery_config(),
            metadata={'kind': 'sql', 'sql': '\n'.join(sql_queries)},
        )
