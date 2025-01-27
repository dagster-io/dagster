from collections.abc import Sequence
from typing import Optional

import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_gcp.bigquery.io_manager import (
    BigQueryClient,
    BigQueryIOManager,
    build_bigquery_io_manager,
)


class BigQueryPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Plugin for the BigQuery I/O Manager that can store and load Pandas DataFrames as BigQuery tables.

    Examples:
        .. code-block:: python

            from dagster_gcp import BigQueryIOManager
            from dagster_bigquery_pandas import BigQueryPandasTypeHandler
            from dagster import Definitions, EnvVar

            class MyBigQueryIOManager(BigQueryIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [BigQueryPandasTypeHandler()]

            @asset(
                key_prefix=["my_dataset"]  # my_dataset will be used as the dataset in BigQuery
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MyBigQueryIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection
    ):
        """Stores the pandas DataFrame in BigQuery."""
        with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")

        job = connection.load_table_from_dataframe(
            dataframe=with_uppercase_cols,
            destination=f"{table_slice.schema}.{table_slice.table}",
            project=table_slice.database,
            location=context.resource_config.get("location") if context.resource_config else None,
            timeout=context.resource_config.get("timeout") if context.resource_config else None,
        )
        job.result()

        context.add_output_metadata(
            {
                # output object may be a slice/partition, so we output different metadata keys based on
                # whether this output represents an entire table or just a slice/partition
                **(
                    TableMetadataSet(partition_row_count=obj.shape[0])
                    if context.has_partition_key
                    else TableMetadataSet(row_count=obj.shape[0])
                ),
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))  # type: ignore  # (bad stubs)
                            for name, dtype in obj.dtypes.items()
                        ]
                    )
                ),
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pd.DataFrame()
        result = connection.query(
            query=BigQueryClient.get_select_statement(table_slice),
            project=table_slice.database,
            location=context.resource_config.get("location") if context.resource_config else None,
            timeout=context.resource_config.get("timeout") if context.resource_config else None,
        ).to_dataframe()

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

        from dagster_gcp_pandas import bigquery_pandas_io_manager
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

    You can set a default dataset to store the assets using the ``dataset`` configuration value of the BigQuery I/O
    Manager. This dataset will be used if no other dataset is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={
                    "io_manager": bigquery_pandas_io_manager.configured({
                        "project" : {"env": "GCP_PROJECT"}
                        "dataset": "my_dataset"
                    })
                }
        )

    On individual assets, you an also specify the dataset where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            # note that the key needs to be "schema"
            metadata={"schema": "my_dataset"}  # will be used as the dataset in BigQuery
        )
        def my_other_table() -> pd.DataFrame:
            ...

    For ops, the dataset can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...

    If none of these is provided, the dataset will default to "public".

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


class BigQueryPandasIOManager(BigQueryIOManager):
    """An I/O manager definition that reads inputs from and writes pandas DataFrames to BigQuery.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_gcp_pandas import BigQueryPandasIOManager
            from dagster import Definitions, EnvVar

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": BigQueryPandasIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

        You can set a default dataset to store the assets using the ``dataset`` configuration value of the BigQuery I/O
        Manager. This dataset will be used if no other dataset is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={
                        "io_manager": BigQueryPandasIOManager(project=EnvVar("GCP_PROJECT", dataset="my_dataset")
                    }
            )

        On individual assets, you an also specify the dataset where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> pd.DataFrame:
                ...

            @asset(
                # note that the key needs to be "schema"
                metadata={"schema": "my_dataset"}  # will be used as the dataset in BigQuery
            )
            def my_other_table() -> pd.DataFrame:
                ...

        For ops, the dataset can be specified by including a "schema" entry in output metadata.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pd.DataFrame:
                ...

        If none of these is provided, the dataset will default to "public".

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

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [BigQueryPandasTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pd.DataFrame
