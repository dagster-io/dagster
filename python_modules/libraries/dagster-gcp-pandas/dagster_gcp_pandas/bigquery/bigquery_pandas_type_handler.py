import pandas as pd
import pandas_gbq
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_gcp.bigquery.io_manager import BigQueryClient, build_bigquery_io_manager


class BigQueryPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Plugin for the BigQuery I/O Manager that can store and load Pandas DataFrames as BigQuery tables.

    Examples:
        .. code-block:: python

            from dagster_gcp import build_bigquery_io_manager
            from dagster_bigquery_pandas import BigQueryPandasTypeHandler
            from dagster import asset, Definitions

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table():
                ...

            bigquery_io_manager = build_bigquery_io_manager([BigQueryPandasTypeHandler()])

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": bigquery_io_manager.configured({
                        "project" : {"env": "GCP_PROJECT"}
                    })
                }
            )

    """

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, _):
        """Stores the pandas DataFrame in BigQuery."""
        with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")

        pandas_gbq.to_gbq(
            with_uppercase_cols,
            destination_table=f"{table_slice.schema}.{table_slice.table}",
            project_id=table_slice.database,
            location=context.resource_config["location"] if context.resource_config else None,
            if_exists="append",
        )

        context.add_output_metadata(
            {
                "row_count": obj.shape[0],
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in obj.dtypes.iteritems()
                        ]
                    )
                ),
            }
        )

    def load_input(self, context: InputContext, table_slice: TableSlice, _) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        result = pandas_gbq.read_gbq(
            BigQueryClient.get_select_statement(table_slice),
            project_id=table_slice.database,
            location=context.resource_config["location"] if context.resource_config else None,
        )
        result.columns = map(str.lower, result.columns)
        return result

    @property
    def supported_types(self):
        return [pd.DataFrame]


bigquery_pandas_io_manager = build_bigquery_io_manager(
    [BigQueryPandasTypeHandler()], default_load_type=pd.DataFrame
)
bigquery_pandas_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes pandas DataFrames to BigQuery.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_bigquery_pandas import bigquery_pandas_io_manager
        from dagster import Definitions

        @asset(
            key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
        )
        def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={
                "io_manager": bigquery_pandas_io_manager.configured({
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
        def make_my_table() -> pd.DataFrame:
            # the returned value will be stored at my_dataset.my_table
            ...

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
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
