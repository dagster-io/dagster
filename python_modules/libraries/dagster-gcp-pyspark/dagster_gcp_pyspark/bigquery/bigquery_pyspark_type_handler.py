from collections.abc import Mapping, Sequence
from typing import Any, Optional

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_gcp import BigQueryIOManager, build_bigquery_io_manager
from dagster_gcp.bigquery.io_manager import BigQueryClient
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType


def _get_bigquery_write_options(
    config: Optional[Mapping[str, Any]], table_slice: TableSlice
) -> Mapping[str, str]:
    conf = {
        "table": f"{table_slice.database}.{table_slice.schema}.{table_slice.table}",
    }
    if config and config.get("temporary_gcs_bucket") is not None:
        conf["temporaryGcsBucket"] = config["temporary_gcs_bucket"]
    else:
        conf["writeMethod"] = "direct"
    return conf


def _get_bigquery_read_options(table_slice: TableSlice) -> Mapping[str, str]:
    conf = {"viewsEnabled": "true", "materializationDataset": table_slice.schema}
    return conf


class BigQueryPySparkTypeHandler(DbTypeHandler[DataFrame]):
    """Plugin for the BigQuery I/O Manager that can store and load PySpark DataFrames as BigQuery tables.

    Examples:
        .. code-block:: python

            from dagster_gcp import BigQueryIOManager
            from dagster_bigquery_pandas import BigQueryPySparkTypeHandler
            from dagster import Definitions, EnvVar

            class MyBigQueryIOManager(BigQueryIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [BigQueryPySparkTypeHandler()]

            @asset(
                key_prefix=["my_dataset"]  # my_dataset will be used as the dataset in BigQuery
            )
            def my_table() -> pyspark.sql.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MyBigQueryIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

    """

    def handle_output(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: OutputContext, table_slice: TableSlice, obj: DataFrame, _
    ) -> Mapping[str, RawMetadataValue]:
        options = _get_bigquery_write_options(context.resource_config, table_slice)

        with_uppercase_cols = obj.toDF(*[c.upper() for c in obj.columns])

        with_uppercase_cols.write.format("bigquery").options(**options).mode("append").save()

        return {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=field.name, type=field.dataType.typeName())
                        for field in obj.schema.fields
                    ]
                )
            ),
        }

    def load_input(self, context: InputContext, table_slice: TableSlice, _) -> DataFrame:  # pyright: ignore[reportIncompatibleMethodOverride]
        options = _get_bigquery_read_options(table_slice)
        spark = SparkSession.builder.getOrCreate()  # type: ignore

        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return spark.createDataFrame([], StructType([]))

        df = (
            spark.read.format("bigquery")
            .options(**options)
            .load(BigQueryClient.get_select_statement(table_slice))
        )

        return df.toDF(*[c.lower() for c in df.columns])

    @property
    def supported_types(self):
        return [DataFrame]


bigquery_pyspark_io_manager = build_bigquery_io_manager(
    [BigQueryPySparkTypeHandler()], default_load_type=DataFrame
)
bigquery_pyspark_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes PySpark DataFrames to BigQuery.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_gcp_pyspark import bigquery_pyspark_io_manager
        from dagster import Definitions

        @asset(
            key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
        )
        def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={
                "io_manager": bigquery_pyspark_io_manager.configured({
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
        def my_table() -> pyspark.sql.DataFrame:
            ...

        @asset(
            # note that the key needs to be "schema"
            metadata={"schema": "my_dataset"}  # will be used as the dataset in BigQuery
        )
        def my_other_table() -> pyspark.sql.DataFrame:
            ...

    For ops, the dataset can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pyspark.sql.DataFrame:
            ...

    If none of these is provided, the dataset will default to "public".

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pyspark.sql.DataFrame) -> pyspark.sql.DataFrame:
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


class BigQueryPySparkIOManager(BigQueryIOManager):
    """An I/O manager definition that reads inputs from and writes PySpark DataFrames to BigQuery.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_gcp_pyspark import BigQueryPySparkIOManager
            from dagster import Definitions, EnvVar

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> pyspark.sql.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": BigQueryPySparkIOManager(project=EnvVar("GCP_PROJECT"))
                }
            )

        You can set a default dataset to store the assets using the ``dataset`` configuration value of the BigQuery I/O
        Manager. This dataset will be used if no other dataset is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={
                        "io_manager": BigQueryPySparkIOManager(project=EnvVar("GCP_PROJECT", dataset="my_dataset")
                    }
            )

        On individual assets, you an also specify the dataset where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_dataset"]  # will be used as the dataset in BigQuery
            )
            def my_table() -> pyspark.sql.DataFrame:
                ...

            @asset(
                # note that the key needs to be "schema"
                metadata={"schema": "my_dataset"}  # will be used as the dataset in BigQuery
            )
            def my_other_table() -> pyspark.sql.DataFrame:
                ...

        For ops, the dataset can be specified by including a "schema" entry in output metadata.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pyspark.sql.DataFrame:
                ...

        If none of these is provided, the dataset will default to "public".

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pyspark.sql.DataFrame) -> pyspark.sql.DataFrame:
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
        return [BigQueryPySparkTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return DataFrame
