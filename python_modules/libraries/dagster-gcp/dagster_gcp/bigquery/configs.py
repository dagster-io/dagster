"""BigQuery configuration.

See the BigQuery Python API documentation for reference:
    https://googleapis.github.io/google-cloud-python/latest/bigquery/reference.html
"""

from dagster import Array, Bool, Field, IntSource, String, StringSource

from .types import (
    BQCreateDisposition,
    BQEncoding,
    BQPriority,
    BQSchemaUpdateOption,
    BQSourceFormat,
    BQWriteDisposition,
    Dataset,
    Table,
)


def bq_resource_config():

    project = Field(
        StringSource,
        description="""Project ID for the project which the client acts on behalf of. Will be passed
        when creating a dataset / job. If not passed, falls back to the default inferred from the
        environment.""",
        is_required=False,
    )

    location = Field(
        StringSource,
        description="(Optional) Default location for jobs / datasets / tables.",
        is_required=False,
    )

    return {"project": project, "location": location}


def _define_shared_fields():
    """The following fields are shared between both QueryJobConfig and LoadJobConfig.
    """

    clustering_fields = Field(
        [String],
        description="""Fields defining clustering for the table

        (Defaults to None).

        Clustering fields are immutable after table creation.
        """,
        is_required=False,
    )

    create_disposition = Field(
        BQCreateDisposition,
        description="""Specifies behavior for creating tables.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.createDisposition
        """,
        is_required=False,
    )

    destination_encryption_configuration = Field(
        StringSource,
        description="""Custom encryption configuration for the destination table.
        Custom encryption configuration (e.g., Cloud KMS keys) or None if using default encryption.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationEncryptionConfiguration
        """,
        is_required=False,
    )

    schema_update_options = Field(
        [BQSchemaUpdateOption],
        description="""Specifies updates to the destination table schema to allow as a side effect
        of the query job.""",
        is_required=False,
    )

    time_partitioning = Field(
        {
            "expiration_ms": Field(
                IntSource,
                description="""Number of milliseconds for which to keep the storage for a
                    partition.""",
                is_required=False,
            ),
            "field": Field(
                StringSource,
                description="""If set, the table is partitioned by this field. If not set, the
                    table is partitioned by pseudo column _PARTITIONTIME. The field must be a
                    top-level TIMESTAMP or DATE field. Its mode must be NONEABLE or REQUIRED.""",
                is_required=False,
            ),
            "require_partition_filter": Field(
                Bool,
                description="""If set to true, queries over the partitioned table require a
                    partition filter that can be used for partition elimination to be specified.""",
                is_required=False,
            ),
        },
        description="Specifies time-based partitioning for the destination table.",
        is_required=False,
    )

    write_disposition = Field(
        BQWriteDisposition,
        description="""
        Action that occurs if the destination table already exists.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.writeDisposition
        """,
        is_required=False,
    )
    return {
        "clustering_fields": clustering_fields,
        "create_disposition": create_disposition,
        "destination_encryption_configuration": destination_encryption_configuration,
        "schema_update_options": schema_update_options,
        "time_partitioning": time_partitioning,
        "write_disposition": write_disposition,
    }


def define_bigquery_query_config():
    """See:
    https://googleapis.github.io/google-cloud-python/latest/bigquery/generated/google.cloud.bigquery.job.QueryJobConfig.html
    """
    sf = _define_shared_fields()

    allow_large_results = Field(
        Bool,
        description="""Allow large query results tables (legacy SQL, only)
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.allowLargeResults
        """,
        is_required=False,
    )

    default_dataset = Field(
        Dataset,
        description="""the default dataset to use for unqualified table names in the query or None
        if not set. The default_dataset setter accepts a str of the fully-qualified dataset ID in
        standard SQL format. The value must included a project ID and dataset ID separated by ".".
        For example: your-project.your_dataset.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.query.defaultDataset
        """,
        is_required=False,
    )

    destination = Field(
        Table,
        description="""table where results are written or None if not set. The destination setter
        accepts a str of the fully-qualified table ID in standard SQL format. The value must
        included a project ID, dataset ID, and table ID, each separated by ".". For example:
        your-project.your_dataset.your_table.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationTable
        """,
        is_required=False,
    )

    dry_run = Field(
        Bool,
        description="""True if this query should be a dry run to estimate costs.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.dryRun
        """,
        is_required=False,
    )

    flatten_results = Field(
        Bool,
        description="""Flatten nested/repeated fields in results. (Legacy SQL only)
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.flattenResults
        """,
        is_required=False,
    )

    maximum_billing_tier = Field(
        IntSource,
        description="""Deprecated. Changes the billing tier to allow high-compute queries.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.maximumBillingTier
        """,
        is_required=False,
    )

    maximum_bytes_billed = Field(
        IntSource,
        description="""Maximum bytes to be billed for this job or None if not set.

        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.maximumBytesBilled
        """,
        is_required=False,
    )

    priority = Field(
        BQPriority,
        description="""Priority of the query.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.priority
        """,
        is_required=False,
    )

    query_parameters = Field(
        [String],
        description="""list of parameters for parameterized query (empty by default)
        See: https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.queryParameters
        """,
        is_required=False,
    )

    # TODO:
    # Type:	Shape[str, google.cloud.bigquery.external_config.ExternalConfig]
    # table_definitions = Field(
    #     PermissiveShape(),
    #     description='''Definitions for external tables or None if not set.
    #     See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.tableDefinitions
    #     ''',
    #     is_required=False,
    # )

    # TODO: Need to add this
    # Type:	[google.cloud.bigquery.query.UDFResource]
    # udf_resources = Field(
    #     String,
    #     description='''user defined function resources (empty by default)
    #     See: https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.userDefinedFunctionResources
    #     ''',
    #     is_required=False
    # )

    use_legacy_sql = Field(
        Bool,
        description="""Use legacy SQL syntax.
        See https://g.co/cloud/bigquery/docs/reference/v2/jobs#configuration.query.useLegacySql
        """,
        is_required=False,
    )

    use_query_cache = Field(
        Bool,
        description="""Look for the query result in the cache.
        See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#configuration.query.useQueryCache
        """,
        is_required=False,
    )

    return {
        "query_job_config": {
            "allow_large_results": allow_large_results,
            "clustering_fields": sf["clustering_fields"],
            "create_disposition": sf["create_disposition"],
            "default_dataset": default_dataset,
            "destination": destination,
            "destination_encryption_configuration": sf["destination_encryption_configuration"],
            "dry_run": dry_run,
            "flatten_results": flatten_results,
            # TODO: labels
            "maximum_billing_tier": maximum_billing_tier,
            "maximum_bytes_billed": maximum_bytes_billed,
            "priority": priority,
            "query_parameters": query_parameters,
            # TODO: table_definitions
            "schema_update_options": sf["schema_update_options"],
            "time_partitioning": sf["time_partitioning"],
            # TODO: udf_resources
            "use_legacy_sql": use_legacy_sql,
            "use_query_cache": use_query_cache,
            "write_disposition": sf["write_disposition"],
        }
    }


def define_bigquery_load_config():
    sf = _define_shared_fields()

    allow_jagged_rows = Field(
        Bool, description="Allow missing trailing optional columns (CSV only).", is_required=False
    )

    allow_quoted_newlines = Field(
        Bool,
        description="Allow quoted data containing newline characters (CSV only).",
        is_required=False,
    )

    autodetect = Field(
        Bool,
        description="Automatically infer the schema from a sample of the data.",
        is_required=False,
    )

    # Destination is a required field for BQ loads
    destination = Field(
        Table,
        description="""table where results are written or None if not set. The destination setter
        accepts a str of the fully-qualified table ID in standard SQL format. The value must
        included a project ID, dataset ID, and table ID, each separated by ".". For example:
        your-project.your_dataset.your_table.
        See https://g.co/cloud/bigquery/docs/reference/rest/v2/jobs#configuration.query.destinationTable
        """,
        is_required=True,
    )

    destination_table_description = Field(
        StringSource, description="description given to destination table.", is_required=False
    )

    destination_table_friendly_name = Field(
        StringSource, description="name given to destination table.", is_required=False
    )

    encoding = Field(
        BQEncoding, description="The character encoding of the data.", is_required=False
    )

    field_delimiter = Field(
        StringSource, description="The separator for fields in a CSV file.", is_required=False
    )

    ignore_unknown_values = Field(
        Bool,
        description="Ignore extra values not represented in the table schema.",
        is_required=False,
    )

    max_bad_records = Field(
        IntSource, description="Number of invalid rows to ignore.", is_required=False
    )

    null_marker = Field(
        StringSource, description="Represents a null value (CSV only).", is_required=False
    )

    quote_character = Field(
        StringSource,
        description="Character used to quote data sections (CSV only).",
        is_required=False,
    )

    schema = Field(
        Array(inner_type=dict), description="Schema of the destination table.", is_required=False
    )

    skip_leading_rows = Field(
        IntSource,
        description="Number of rows to skip when reading data (CSV only).",
        is_required=False,
    )

    source_format = Field(BQSourceFormat, description="File format of the data.", is_required=False)

    use_avro_logical_types = Field(
        Bool,
        description="""For loads of Avro data, governs whether Avro logical types are converted to
        their corresponding BigQuery types(e.g. TIMESTAMP) rather than raw types (e.g. INTEGER).""",
        is_required=False,
    )

    return {
        "destination": destination,
        "load_job_config": {
            "allow_jagged_rows": allow_jagged_rows,
            "allow_quoted_newlines": allow_quoted_newlines,
            "autodetect": autodetect,
            "clustering_fields": sf["clustering_fields"],
            "create_disposition": sf["create_disposition"],
            "destination_encryption_configuration": sf["destination_encryption_configuration"],
            "destination_table_description": destination_table_description,
            "destination_table_friendly_name": destination_table_friendly_name,
            "encoding": encoding,
            "field_delimiter": field_delimiter,
            "ignore_unknown_values": ignore_unknown_values,
            "max_bad_records": max_bad_records,
            "null_marker": null_marker,
            "quote_character": quote_character,
            "schema": schema,
            "schema_update_options": sf["schema_update_options"],
            "skip_leading_rows": skip_leading_rows,
            "source_format": source_format,
            "time_partitioning": sf["time_partitioning"],
            "use_avro_logical_types": use_avro_logical_types,
            "write_disposition": sf["write_disposition"],
        },
    }


def define_bigquery_create_dataset_config():
    dataset = Field(Dataset, description="A dataset to create.", is_required=True)

    exists_ok = Field(
        Bool,
        description="""Defaults to False. If True, ignore "already exists" errors when creating the
        dataset.""",
        is_required=False,
    )

    return {"dataset": dataset, "exists_ok": exists_ok}


def define_bigquery_delete_dataset_config():
    dataset = Field(Dataset, description="A dataset to delete.", is_required=True)

    delete_contents = Field(
        Bool,
        description="""If True, delete all the tables in the dataset. If False and the dataset
        contains tables, the request will fail. Default is False.""",
        is_required=False,
    )

    not_found_ok = Field(
        Bool,
        description="""Defaults to False. If True, ignore "not found" errors when deleting the
        dataset.""",
        is_required=False,
    )

    return {
        "dataset": dataset,
        "delete_contents": delete_contents,
        "not_found_ok": not_found_ok,
    }
