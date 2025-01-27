from collections.abc import Sequence
from typing import Optional

import polars as pl
from dagster import InputContext, MetadataValue, OutputContext
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice

from dagster_polars.io_managers.utils import get_polars_metadata

try:
    from dagster_gcp.bigquery.io_manager import BigQueryClient, BigQueryIOManager
    from google.cloud import bigquery as bigquery
except ImportError as e:
    raise ImportError("Install 'dagster-polars[gcp]' to use BigQuery functionality") from e


class PolarsBigQueryTypeHandler(DbTypeHandler[pl.DataFrame]):
    """Plugin for the BigQuery I/O Manager that can store and load Polars DataFrames as BigQuery tables.

    Examples:
        .. code-block:: python

            from dagster_gcp import BigQueryIOManager
            from dagster_bigquery_polars import BigQueryPolarsTypeHandler
            from dagster import Definitions, EnvVar

            class MyBigQueryIOManager(BigQueryIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [PolarsBigQueryTypeHandler()]

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
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: Optional[pl.DataFrame],
        connection,
    ):
        """Stores the polars DataFrame in BigQuery."""
        skip_upload = False
        if obj is None:
            context.log.warning("Skipping BigQuery output as the output is None")
            skip_upload = True
        elif len(obj) == 0:
            context.log.warning("Skipping BigQuery output as the output DataFrame is empty")
            skip_upload = True

        if skip_upload:
            context.add_output_metadata({"missing": MetadataValue.bool(True)})
            return

        assert obj is not None
        assert isinstance(connection, bigquery.Client)
        assert context.definition_metadata is not None
        job_config = bigquery.LoadJobConfig(
            write_disposition=context.definition_metadata.get("write_disposition")
        )

        # FIXME: load_table_from_dataframe writes the dataframe to a temporary parquet file
        # and then calls load_table_from_file. This can cause problems in cloud environments
        # therefore, it's better to use load_table_from_uri with GCS,
        # but this requires the remote filesystem to be available in this code
        job = connection.load_table_from_dataframe(
            dataframe=obj.to_pandas(),
            destination=f"{table_slice.schema}.{table_slice.table}",
            project=table_slice.database,
            location=context.resource_config.get("location") if context.resource_config else None,  # type: ignore
            timeout=context.resource_config.get("timeout") if context.resource_config else None,  # type: ignore
            job_config=job_config,
        )
        job.result()

        context.add_output_metadata(get_polars_metadata(context=context, df=obj))

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pl.DataFrame:
        """Loads the input as a Polars DataFrame."""
        assert isinstance(connection, bigquery.Client)

        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pl.DataFrame()
        result = connection.query(
            query=BigQueryClient.get_select_statement(table_slice),
            project=table_slice.database,
            location=context.resource_config.get("location") if context.resource_config else None,
            timeout=context.resource_config.get("timeout") if context.resource_config else None,
        ).to_arrow()

        return pl.DataFrame(result)

    @property
    def supported_types(self) -> list:
        return [pl.DataFrame]


class PolarsBigQueryIOManager(BigQueryIOManager):
    """Implements reading and writing Polars DataFrames from/to `BigQuery <https://cloud.google.com/bigquery>`_).

    Features:
    - All :py:class:`~dagster.DBIOManager` features
    - Supports writing partitioned tables (`"partition_expr"` input metadata key must be specified).

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster import Definitions, EnvVar
            from dagster_polars import PolarsBigQueryIOManager

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": PolarsBigQueryIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

        You can tell Dagster in which dataset to create tables by setting the "dataset" configuration value.
        If you do not provide a dataset as configuration to the I/O manager, Dagster will determine a dataset based
        on the assets and ops using the I/O Manager. For assets, the dataset will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the dataset. For example,
        if the asset "my_table" had the key prefix ["gcp", "bigquery", "my_dataset"], the dataset "my_dataset" will be
        used. For ops, the dataset can be specified by including a "schema" entry in output metadata. If "schema" is
        not provided via config or on the asset/op, "public" will be used for the dataset.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_dataset"})}
            )
            def make_my_table() -> pl.DataFrame:
                # the returned value will be stored at my_dataset.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pl.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

        If you cannot upload a file to your Dagster deployment, or otherwise cannot
        `authenticate with GCP <https://cloud.google.com/docs/authentication/provide-credentials-adc>`_
        via a standard method, you can provide a service account key as the "gcp_credentials" configuration.
        Dagster will store this key in a temporary file and set GOOGLE_APPLICATION_CREDENTIALS to point to the file.
        After the run completes, the file will be deleted, and GOOGLE_APPLICATION_CREDENTIALS will be
        unset. The key must be base64 encoded to avoid issues with newlines in the keys. You can retrieve
        the base64 encoded key with this shell command: cat $GOOGLE_APPLICATION_CREDENTIALS | base64

        The "write_disposition" metadata key can be used to set the `write_disposition` parameter
        of `bigquery.JobConfig`. For example, set it to `"WRITE_APPEND"` to append to an existing table intead of
        overwriting it.

    Install `dagster-polars[gcp]` to use this IOManager.

    """

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [PolarsBigQueryTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pl.DataFrame
