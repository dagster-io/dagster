from dagster import Bool, Dict, Field, List, Int, String

from .types import (
    Dataset,
    Table,
    BQCreateDisposition,
    BQPriority,
    BQSchemaUpdateOption,
    BQWriteDisposition,
)


def _define_bigquery_base_fields(subset=None):
    '''BigQuery configuration.

    See the BigQuery Python API documentation for reference:
        https://googleapis.github.io/google-cloud-python/latest/bigquery/reference.html
    '''
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

    allow_large_results = Field(
        Bool,
        description='''Allow large query results tables (legacy SQL, only)
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.allowLargeResults
        ''',
        is_optional=True,
    )

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

    destination_encryption_configuration = Field(
        String,
        description='''Custom encryption configuration for the destination table.
        Custom encryption configuration (e.g., Cloud KMS keys) or None if using default encryption.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationEncryptionConfiguration
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

    schema_update_options = Field(
        List(BQSchemaUpdateOption),
        description='''Specifies updates to the destination table schema to allow as a side effect
        of the query job.''',
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
    # Type:	google.cloud.bigquery.table.TimePartitioning
    # time_partitioning = Field(
    #     description='Specifies time-based partitioning for the destination table.'
    #     is_optional=True
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

    write_disposition = Field(
        BQWriteDisposition,
        description='''
        Action that occurs if the destination table already exists.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.writeDisposition
        ''',
        is_optional=True,
    )
    fields = {
        'project': project,
        'location': location,
        'allow_large_results': allow_large_results,
        'clustering_fields': clustering_fields,
        'create_disposition': create_disposition,
        'default_dataset': default_dataset,
        'destination': destination,
        'destination_encryption_configuration': destination_encryption_configuration,
        'dry_run': dry_run,
        'flatten_results': flatten_results,
        'maximum_billing_tier': maximum_billing_tier,
        'maximum_bytes_billed': maximum_bytes_billed,
        'priority': priority,
        'query_parameters': query_parameters,
        'schema_update_options': schema_update_options,
        'use_legacy_sql': use_legacy_sql,
        'use_query_cache': use_query_cache,
        'write_disposition': write_disposition,
    }

    # if subset keys are provided, only return those
    return fields if subset is None else {k: v for k, v in fields.items() if k in subset}


def define_bigquery_config():
    fields = _define_bigquery_base_fields()
    return Field(Dict(fields=fields), description='BigQuery configuration')


def define_bigquery_load_config():
    fields = _define_bigquery_base_fields()

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
    fields['destination'] = destination
    return Field(Dict(fields=fields), description='BigQuery load configuration')


def define_bigquery_create_dataset_config():
    fields = _define_bigquery_base_fields({'project', 'location', 'dry_run'})

    dataset = Field(Dataset, description='A dataset to create.', is_optional=False)

    exists_ok = Field(
        Bool,
        description='''Defaults to False. If True, ignore “already exists” errors when creating the
        dataset.''',
        is_optional=True,
    )
    fields['dataset'] = dataset
    fields['exists_ok'] = exists_ok
    return Field(Dict(fields=fields), description='BigQuery create dataset configuration')
