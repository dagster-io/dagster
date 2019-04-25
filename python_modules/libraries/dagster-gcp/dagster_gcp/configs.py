'''BigQuery configuration.

See the BigQuery Python API documentation for reference:
    https://googleapis.github.io/google-cloud-python/latest/bigquery/reference.html
'''

from dagster import Bool, Dict, Field, List, Int, String

from .types import (
    Dataset,
    Table,
    BQCreateDisposition,
    BQEncoding,
    BQPriority,
    BQSchemaUpdateOption,
    BQSourceFormat,
    BQWriteDisposition,
)


def bq_resource_config():

    project = Field(
        String,
        description='''Project ID for the project which the client acts on behalf of. Will be passed
        when creating a dataset / job. If not passed, falls back to the default inferred from the
        environment.''',
        is_optional=True,
    )

    location = Field(
        String,
        description='(Optional) Default location for jobs / datasets / tables.',
        is_optional=True,
    )

    return Field(Dict(fields={'project': project, 'location': location}))


def _define_shared_fields():
    '''The following fields are shared between both QueryJobConfig and LoadJobConfig.
    '''

    clustering_fields = Field(
        List(String),
        description='''Fields defining clustering for the table

        (Defaults to None).

        Clustering fields are immutable after table creation.
        ''',
        is_optional=True,
    )

    create_disposition = Field(
        BQCreateDisposition,
        description='''Specifies behavior for creating tables.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.createDisposition
        ''',
        is_optional=True,
    )

    destination_encryption_configuration = Field(
        String,
        description='''Custom encryption configuration for the destination table.
        Custom encryption configuration (e.g., Cloud KMS keys) or None if using default encryption.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationEncryptionConfiguration
        ''',
        is_optional=True,
    )

    schema_update_options = Field(
        List(BQSchemaUpdateOption),
        description='''Specifies updates to the destination table schema to allow as a side effect
        of the query job.''',
        is_optional=True,
    )

    time_partitioning = Field(
        Dict(
            fields={
                'expiration_ms': Field(
                    Int,
                    description='''Number of milliseconds for which to keep the storage for a
                    partition.''',
                    is_optional=True,
                ),
                'field': Field(
                    String,
                    description='''If set, the table is partitioned by this field. If not set, the
                    table is partitioned by pseudo column _PARTITIONTIME. The field must be a
                    top-level TIMESTAMP or DATE field. Its mode must be NULLABLE or REQUIRED.''',
                    is_optional=True,
                ),
                'require_partition_filter': Field(
                    Bool,
                    description='''If set to true, queries over the partitioned table require a
                    partition filter that can be used for partition elimination to be specified.''',
                    is_optional=True,
                ),
            }
        ),
        description='Specifies time-based partitioning for the destination table.',
        is_optional=True,
    )

    write_disposition = Field(
        BQWriteDisposition,
        description='''
        Action that occurs if the destination table already exists.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.writeDisposition
        ''',
        is_optional=True,
    )
    return {
        'clustering_fields': clustering_fields,
        'create_disposition': create_disposition,
        'destination_encryption_configuration': destination_encryption_configuration,
        'schema_update_options': schema_update_options,
        'time_partitioning': time_partitioning,
        'write_disposition': write_disposition,
    }


def define_bigquery_query_config():
    '''See:
    https://googleapis.github.io/google-cloud-python/latest/bigquery/generated/google.cloud.bigquery.job.QueryJobConfig.html
    '''
    sf = _define_shared_fields()

    allow_large_results = Field(
        Bool,
        description='''Allow large query results tables (legacy SQL, only)
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.allowLargeResults
        ''',
        is_optional=True,
    )

    default_dataset = Field(
        Dataset,
        description='''the default dataset to use for unqualified table names in the query or None
        if not set. The default_dataset setter accepts a str of the fully-qualified dataset ID in
        standard SQL format. The value must included a project ID and dataset ID separated by ".".
        For example: your-project.your_dataset.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.query.defaultDataset
        ''',
        is_optional=True,
    )

    destination = Field(
        Table,
        description='''table where results are written or None if not set. The destination setter
        accepts a str of the fully-qualified table ID in standard SQL format. The value must
        included a project ID, dataset ID, and table ID, each separated by ".". For example:
        your-project.your_dataset.your_table.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationTable
        ''',
        is_optional=True,
    )

    dry_run = Field(
        Bool,
        description='''True if this query should be a dry run to estimate costs.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.dryRun
        ''',
        is_optional=True,
    )

    flatten_results = Field(
        Bool,
        description='''Flatten nested/repeated fields in results. (Legacy SQL only)
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.flattenResults
        ''',
        is_optional=True,
    )

    maximum_billing_tier = Field(
        Int,
        description='''Deprecated. Changes the billing tier to allow high-compute queries.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.maximumBillingTier
        ''',
        is_optional=True,
    )

    maximum_bytes_billed = Field(
        Int,
        description='''Maximum bytes to be billed for this job or None if not set.

        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.maximumBytesBilled
        ''',
        is_optional=True,
    )

    priority = Field(
        BQPriority,
        description='''Priority of the query.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.priority
        ''',
        is_optional=True,
    )

    query_parameters = Field(
        List(String),
        description='''list of parameters for parameterized query (empty by default)
        See: https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.queryParameters
        ''',
        is_optional=True,
    )

    # TODO:
    # Type:	Dict[str, google.cloud.bigquery.external_config.ExternalConfig]
    # table_definitions = Field(
    #     PermissiveDict(),
    #     description='''Definitions for external tables or None if not set.
    #     See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.tableDefinitions
    #     ''',
    #     is_optional=True,
    # )

    # TODO: Need to add this
    # Type:	List[google.cloud.bigquery.query.UDFResource]
    # udf_resources = Field(
    #     String,
    #     description='''user defined function resources (empty by default)
    #     See: https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.userDefinedFunctionResources
    #     ''',
    #     is_optional=True
    # )

    use_legacy_sql = Field(
        Bool,
        description='''Use legacy SQL syntax.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.query.useLegacySql
        ''',
        is_optional=True,
    )

    use_query_cache = Field(
        Bool,
        description='''Look for the query result in the cache.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.useQueryCache
        ''',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'query_job_config': Field(
                    Dict(
                        fields={
                            'allow_large_results': allow_large_results,
                            'clustering_fields': sf['clustering_fields'],
                            'create_disposition': sf['create_disposition'],
                            'default_dataset': default_dataset,
                            'destination': destination,
                            'destination_encryption_configuration': sf[
                                'destination_encryption_configuration'
                            ],
                            'dry_run': dry_run,
                            'flatten_results': flatten_results,
                            # TODO: labels
                            'maximum_billing_tier': maximum_billing_tier,
                            'maximum_bytes_billed': maximum_bytes_billed,
                            'priority': priority,
                            'query_parameters': query_parameters,
                            # TODO: table_definitions
                            'schema_update_options': sf['schema_update_options'],
                            'time_partitioning': sf['time_partitioning'],
                            # TODO: udf_resources
                            'use_legacy_sql': use_legacy_sql,
                            'use_query_cache': use_query_cache,
                            'write_disposition': sf['write_disposition'],
                        }
                    )
                )
            }
        ),
        description='BigQuery query configuration',
    )


def define_bigquery_load_config():
    sf = _define_shared_fields()

    allow_jagged_rows = Field(
        Bool, description='Allow missing trailing optional columns (CSV only).', is_optional=True
    )

    allow_quoted_newlines = Field(
        Bool,
        description='Allow quoted data containing newline characters (CSV only).',
        is_optional=True,
    )

    autodetect = Field(
        Bool,
        description='Automatically infer the schema from a sample of the data.',
        is_optional=True,
    )

    # Destination is a required field for BQ loads
    destination = Field(
        Table,
        description='''table where results are written or None if not set. The destination setter
        accepts a str of the fully-qualified table ID in standard SQL format. The value must
        included a project ID, dataset ID, and table ID, each separated by ".". For example:
        your-project.your_dataset.your_table.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationTable
        ''',
        is_optional=False,
    )

    destination_table_description = Field(
        String, description='description given to destination table.', is_optional=True
    )

    destination_table_friendly_name = Field(
        String, description='name given to destination table.', is_optional=True
    )

    encoding = Field(
        BQEncoding, description='The character encoding of the data.', is_optional=True
    )

    field_delimiter = Field(
        String, description='The separator for fields in a CSV file.', is_optional=True
    )

    ignore_unknown_values = Field(
        Bool,
        description='Ignore extra values not represented in the table schema.',
        is_optional=True,
    )

    max_bad_records = Field(Int, description='Number of invalid rows to ignore.', is_optional=True)

    null_marker = Field(String, description='Represents a null value (CSV only).', is_optional=True)

    quote_character = Field(
        String, description='Character used to quote data sections (CSV only).', is_optional=True
    )

    skip_leading_rows = Field(
        Int, description='Number of rows to skip when reading data (CSV only).', is_optional=True
    )

    source_format = Field(BQSourceFormat, description='File format of the data.', is_optional=True)

    use_avro_logical_types = Field(
        Bool,
        description='''For loads of Avro data, governs whether Avro logical types are converted to
        their corresponding BigQuery types(e.g. TIMESTAMP) rather than raw types (e.g. INTEGER).''',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'destination': destination,
                'load_job_config': Field(
                    Dict(
                        fields={
                            'allow_jagged_rows': allow_jagged_rows,
                            'allow_quoted_newlines': allow_quoted_newlines,
                            'autodetect': autodetect,
                            'clustering_fields': sf['clustering_fields'],
                            'create_disposition': sf['create_disposition'],
                            'destination_encryption_configuration': sf[
                                'destination_encryption_configuration'
                            ],
                            'destination_table_description': destination_table_description,
                            'destination_table_friendly_name': destination_table_friendly_name,
                            'encoding': encoding,
                            'field_delimiter': field_delimiter,
                            'ignore_unknown_values': ignore_unknown_values,
                            'max_bad_records': max_bad_records,
                            'null_marker': null_marker,
                            'quote_character': quote_character,
                            # TODO: schema
                            'schema_update_options': sf['schema_update_options'],
                            'skip_leading_rows': skip_leading_rows,
                            'source_format': source_format,
                            'time_partitioning': sf['time_partitioning'],
                            'use_avro_logical_types': use_avro_logical_types,
                            'write_disposition': sf['write_disposition'],
                        }
                    )
                ),
            }
        ),
        description='BigQuery load configuration',
    )


def define_bigquery_create_dataset_config():
    dataset = Field(Dataset, description='A dataset to create.', is_optional=False)

    exists_ok = Field(
        Bool,
        description='''Defaults to False. If True, ignore “already exists” errors when creating the
        dataset.''',
        is_optional=True,
    )

    return Field(
        Dict(fields={'dataset': dataset, 'exists_ok': exists_ok}),
        description='BigQuery create dataset configuration',
    )


def define_bigquery_delete_dataset_config():
    dataset = Field(Dataset, description='A dataset to delete.', is_optional=False)

    delete_contents = Field(
        Bool,
        description='''If True, delete all the tables in the dataset. If False and the dataset
        contains tables, the request will fail. Default is False.''',
        is_optional=True,
    )

    not_found_ok = Field(
        Bool,
        description='''Defaults to False. If True, ignore “not found” errors when deleting the
        dataset.''',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'dataset': dataset,
                'delete_contents': delete_contents,
                'not_found_ok': not_found_ok,
            }
        ),
        description='BigQuery delete dataset configuration',
    )
