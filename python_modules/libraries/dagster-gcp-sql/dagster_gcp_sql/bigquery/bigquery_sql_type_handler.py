from typing import Any, Mapping, Optional, Sequence, Type

import pandas as pd
from dagster import InputContext, MarkdownMetadataValue, OutputContext
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster._core.storage.sql import SqlQuery
from dagster_gcp.bigquery.io_manager import (
    BigQueryClient,
    BigQueryIOManager,
    build_bigquery_io_manager,
)
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


class BigQuerySqlTypeHandler(DbTypeHandler[SqlQuery]):
    """Executes SQL INSERT INTO queries in BigQuery and constructs SQL SELECT queries.

    Examples:
        .. code-block:: python

            from dagster_gcp import BigQueryIOManager
            from dagster_bigquery_sql import BigQuerySqlTypeHandler
            from dagster import Definitions, EnvVar

            class MyBigQueryIOManager(BigQueryIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [BigQuerySqlTypeHandler()]

            @asset(
                key_prefix=["my_dataset"]  # my_dataset will be used as the dataset in BigQuery
            )
            def my_table() -> SqlQuery:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MyBigQueryIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

    """

    @staticmethod
    def _schemas_are_compatible(table, query_str, connection):
        """Check that the incoming schema is equal to the existing schema.
        """
        dry_run_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = connection.query(query_str, job_config=dry_run_config)

        insert_fields = {field.name: (field.field_type, field.mode) for field in query_job.schema}
        dest_fields = {field.name: (field.field_type, field.mode) for field in table.schema}

        if insert_fields == dest_fields:
            return True

        raise ValueError(
            f"Schemas do not match. "
            f"Incoming: {query_job.schema}. "
            f"Existing: {table.schema}"
        )

    def _insert_query(
        self,
        query: SqlQuery,
        table_slice: TableSlice,
        connection: bigquery.Client
    ) -> None:
        """Create and execute an insert values query from the parsed query.
        """
        query_str = query.parse_bindings()
        table_name = f"{table_slice.schema}.{table_slice.table}"
        try:
            table = connection.get_table(table_name)

            # Table exists, so check the schemas match
            # Then insert the data
            if self._schemas_are_compatible(table, query_str, connection):
                insert_query = (f"INSERT INTO {table_name} ({query_str})")
                query_job = connection.query(insert_query)


        except NotFound:
            # table does not exist, so create
            insert_query = (f"CREATE TABLE IF NOT EXISTS {table_name} as ({query_str})")
            query_job = connection.query(insert_query)


        # wait for completion
        query_job.result()

    @staticmethod
    def _get_metadata(
            query: SqlQuery,
            table_slice: TableSlice,
            connection: bigquery.Client
        ) -> Mapping[str, Any]:
        """Get metadata from a table
        """
        query_str = query.parse_bindings()
        for row in connection.query(f"SELECT COUNT(*) FROM ({query_str});").result():
            row_count = row[0]

        table_schema = connection.get_table(f"{table_slice.schema}.{table_slice.table}").schema
        schema_df = pd.DataFrame(
            [(field.name, field.field_type) for field in table_schema],
            columns=["column_name", "data_type"]
        )

        return {
            "row_count": row_count,
            "col_count": len(table_schema),
            "schema": MarkdownMetadataValue(schema_df[["column_name", "data_type"]].to_markdown())
        }

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: SqlQuery, connection
    ):
        """Stores the pandas DataFrame in BigQuery."""
        # with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
        self._insert_query(obj, table_slice, connection)
        metadata = self._get_metadata(obj, table_slice, connection)
        context.add_output_metadata(metadata)

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> SqlQuery:
        """Loads the input as a Pandas DataFrame."""
        query_str = BigQueryClient.get_select_statement(table_slice)
        return SqlQuery(query_str)

    @property
    def supported_types(self):
        return [SqlQuery]


bigquery_sql_io_manager = build_bigquery_io_manager(
    [BigQuerySqlTypeHandler()], default_load_type=SqlQuery
)
bigquery_sql_io_manager.__doc__ = """
An I/O manager definition that executes SQL INSERT INTO queries in BigQuery and constructs SQL SELECT queries.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_gcp_sql import bigquery_sql_io_manager
        from dagster import Definitions

        @asset(
            key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
        )
        def my_table() -> SqlQuery:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={
                "io_manager": bigquery_sql_io_manager.configured({
                    "project" : {"env": "GCP_PROJECT"}
                })
            }
        )

    You can tell Dagster in which dataset to create tables by setting the "dataset" configuration value.
    If you do not provide a dataset as configuration to the I/O manager, Dagster will determine a dataset based
    on the assets and ops using the I/O Manager. For assets, the dataset will be determined from the asset key,
    as shown in the above example. The final prefix before the asset name will be used as the dataset. For example,
    if the asset "my_table" had the key prefix ["gcp", "bigquery", "my_dataset"], the dataset "my_dataset" will be
    used. For ops, the dataset can be specified by including a "schema" entry in output metadata. If "schema" is not provided
    via config or on the asset/op, "public" will be used for the dataset.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_dataset"})}
        )
        def make_my_table() -> SqlQuery:
            # the returned value will be stored at my_dataset.my_table
            ...

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: SqlQuery) -> SqlQuery:
            # my_table will just contain the data from column "a"
            ...

    If you cannot upload a file to your Dagster deployment, or otherwise cannot
    `authenticate with GCP <https://cloud.google.com/docs/authentication/provide-credentials-adc>`_
    via a standard method, you can provide a service account key as the "gcp_credentials" configuration.
    Dagster will store this key in a temporary file and set GOOGLE_APPLICATION_CREDENTIALS to point to the file.
    After the run completes, the file will be deleted, and GOOGLE_APPLICATION_CREDENTIALS will be
    unset. The key must be base64 encoded to avoid issues with newlines in the keys. You can retrieve
    the base64 encoded key with this shell command: cat $GOOGLE_APPLICATION_CREDENTIALS | base64

"""


class BigQuerySqlIOManager(BigQueryIOManager):
    """An I/O manager definition that executes SQL INSERT INTO queries in BigQuery and constructs SQL SELECT queries.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_gcp_sql import BigQuerySqlIOManager
            from dagster import Definitions, EnvVar

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> SqlQuery:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": BigQuerySqlIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

        You can tell Dagster in which dataset to create tables by setting the "dataset" configuration value.
        If you do not provide a dataset as configuration to the I/O manager, Dagster will determine a dataset based
        on the assets and ops using the I/O Manager. For assets, the dataset will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the dataset. For example,
        if the asset "my_table" had the key prefix ["gcp", "bigquery", "my_dataset"], the dataset "my_dataset" will be
        used. For ops, the dataset can be specified by including a "schema" entry in output metadata. If "schema" is not provided
        via config or on the asset/op, "public" will be used for the dataset.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_dataset"})}
            )
            def make_my_table() -> SqlQuery:
                # the returned value will be stored at my_dataset.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: SqlQuery) -> SqlQuery:
                # my_table will just contain the data from column "a"
                ...

        If you cannot upload a file to your Dagster deployment, or otherwise cannot
        `authenticate with GCP <https://cloud.google.com/docs/authentication/provide-credentials-adc>`_
        via a standard method, you can provide a service account key as the "gcp_credentials" configuration.
        Dagster will store this key in a temporary file and set GOOGLE_APPLICATION_CREDENTIALS to point to the file.
        After the run completes, the file will be deleted, and GOOGLE_APPLICATION_CREDENTIALS will be
        unset. The key must be base64 encoded to avoid issues with newlines in the keys. You can retrieve
        the base64 encoded key with this shell command: cat $GOOGLE_APPLICATION_CREDENTIALS | base64

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [BigQuerySqlTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return SqlQuery
