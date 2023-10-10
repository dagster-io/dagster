from abc import abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional, Sequence, Type, cast

from dagster import IOManagerDefinition, OutputContext, io_manager
from dagster._annotations import experimental
from dagster._config.pythonic_config import (
    ConfigurableIOManagerFactory,
)
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
    TimeWindow,
)
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from pydantic import Field

from .utils import setup_gcp_creds

BIGQUERY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@experimental
def build_bigquery_io_manager(
    type_handlers: Sequence[DbTypeHandler], default_load_type: Optional[Type] = None
) -> IOManagerDefinition:
    """Builds an I/O manager definition that reads inputs from and writes outputs to BigQuery.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            slices of BigQuery tables and an in-memory type - e.g. a Pandas DataFrame.
            If only one DbTypeHandler is provided, it will be used as the default_load_type.
        default_load_type (Type): When an input has no type annotation, load it as this type.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_gcp import build_bigquery_io_manager
            from dagster_bigquery_pandas import BigQueryPandasTypeHandler
            from dagster import Definitions

            @asset(
                key_prefix=["my_dataset"]  # my_dataset will be used as the dataset in BigQuery
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
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

        You can tell Dagster in which dataset to create tables by setting the ``dataset`` configuration value.
        If you do not provide a dataset as configuration to the I/O manager, Dagster will determine a dataset based
        on the assets and ops using the I/O Manager. For assets, the dataset will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the dataset. For example,
        if the asset ``my_table`` had the key prefix ``["gcp", "bigquery", "my_dataset"]``, the dataset ``my_dataset`` will be
        used. For ops, the dataset can be specified by including a `schema` entry in output metadata. If ``schema`` is
        not provided via config or on the asset/op, ``public`` will be used for the dataset.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_dataset"})}
            )
            def make_my_table() -> pd.DataFrame:
                # the returned value will be stored at my_dataset.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata ``columns`` to the
        :py:class:`~dagster.In` or :py:class:`~dagster.AssetIn`.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

        If you cannot upload a file to your Dagster deployment, or otherwise cannot
        `authenticate with GCP <https://cloud.google.com/docs/authentication/provide-credentials-adc>`_
        via a standard method, you can provide a service account key as the ``gcp_credentials`` configuration.
        Dagster willstore this key in a temporary file and set ``GOOGLE_APPLICATION_CREDENTIALS`` to point to the file.
        After the run completes, the file will be deleted, and ``GOOGLE_APPLICATION_CREDENTIALS`` will be
        unset. The key must be base64 encoded to avoid issues with newlines in the keys. You can retrieve
        the base64 encoded with this shell command: ``cat $GOOGLE_APPLICATION_CREDENTIALS | base64``
    """

    @dagster_maintained_io_manager
    @io_manager(config_schema=BigQueryIOManager.to_config_schema())
    def bigquery_io_manager(init_context):
        """I/O Manager for storing outputs in a BigQuery database.

        Assets will be stored in the dataset and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the dataset specified by output metadata (defaults to public) in a
        table of the name of the output.

        Note that the BigQuery config is mapped to the DB IO manager table hierarchy as follows:
          BigQuery   DB IO
        * project -> database
        * dataset -> schema
        * table -> table
        """
        mgr = DbIOManager(
            type_handlers=type_handlers,
            db_client=BigQueryClient(),
            io_manager_name="BigQueryIOManager",
            database=init_context.resource_config["project"],
            schema=init_context.resource_config.get("dataset"),
            default_load_type=default_load_type,
        )
        if init_context.resource_config.get("gcp_credentials"):
            with setup_gcp_creds(init_context.resource_config.get("gcp_credentials")):
                yield mgr
        else:
            yield mgr

    return bigquery_io_manager


class BigQueryIOManager(ConfigurableIOManagerFactory):
    """Base class for an I/O manager definition that reads inputs from and writes outputs to BigQuery.

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

        You can tell Dagster in which dataset to create tables by setting the ``dataset`` configuration value.
        If you do not provide a dataset as configuration to the I/O manager, Dagster will determine a dataset based
        on the assets and ops using the I/O Manager. For assets, the dataset will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the dataset. For example,
        if the asset ``my_table`` had the key prefix ``["gcp", "bigquery", "my_dataset"]``, the dataset ``my_dataset`` will be
        used. For ops, the dataset can be specified by including a ``schema`` entry in output metadata. If ``schema`` is
        not provided via config or on the asset/op, ``public`` will be used for the dataset.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_dataset"})}
            )
            def make_my_table() -> pd.DataFrame:
                # the returned value will be stored at my_dataset.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata ``columns`` to the
        :py:class:`~dagster.In` or :py:class:`~dagster.AssetIn`.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

        If you cannot upload a file to your Dagster deployment, or otherwise cannot
        `authenticate with GCP <https://cloud.google.com/docs/authentication/provide-credentials-adc>`_
        via a standard method, you can provide a service account key as the ``gcp_credentials`` configuration.
        Dagster will store this key in a temporary file and set ``GOOGLE_APPLICATION_CREDENTIALS`` to point to the file.
        After the run completes, the file will be deleted, and ``GOOGLE_APPLICATION_CREDENTIALS`` will be
        unset. The key must be base64 encoded to avoid issues with newlines in the keys. You can retrieve
        the base64 encoded with this shell command: ``cat $GOOGLE_APPLICATION_CREDENTIALS | base64``
    """

    project: str = Field(description="The GCP project to use.")
    dataset: Optional[str] = Field(
        default=None,
        description=(
            "Name of the BigQuery dataset to use. If not provided, the last prefix before"
            " the asset name will be used."
        ),
    )
    location: Optional[str] = Field(
        default=None,
        description=(
            "The GCP location. Note: When using PySpark DataFrames, the default"
            " location of the project will be used. A custom location can be specified in"
            " your SparkSession configuration."
        ),
    )
    gcp_credentials: Optional[str] = Field(
        default=None,
        description=(
            "GCP authentication credentials. If provided, a temporary file will be created"
            " with the credentials and ``GOOGLE_APPLICATION_CREDENTIALS`` will be set to the"
            " temporary file. To avoid issues with newlines in the keys, you must base64"
            " encode the key. You can retrieve the base64 encoded key with this shell"
            " command: ``cat $GOOGLE_AUTH_CREDENTIALS | base64``"
        ),
    )
    temporary_gcs_bucket: Optional[str] = Field(
        default=None,
        description=(
            "When using PySpark DataFrames, optionally specify a temporary GCS bucket to"
            " store data. If not provided, data will be directly written to BigQuery."
        ),
    )
    timeout: Optional[float] = Field(
        default=None,
        description=(
            "When using Pandas DataFrames, optionally specify a timeout for the BigQuery"
            " queries (loading and reading from tables)."
        ),
    )

    @staticmethod
    @abstractmethod
    def type_handlers() -> Sequence[DbTypeHandler]: ...

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return None

    def create_io_manager(self, context) -> Generator:
        mgr = DbIOManager(
            db_client=BigQueryClient(),
            io_manager_name="BigQueryIOManager",
            database=self.project,
            schema=self.dataset,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
        )
        if self.gcp_credentials:
            with setup_gcp_creds(self.gcp_credentials):
                yield mgr
        else:
            yield mgr


class BigQueryClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        try:
            connection.query(_get_cleanup_statement(table_slice)).result()
        except NotFound:
            # table doesn't exist yet, so ignore the error
            pass

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"

        if table_slice.partition_dimensions and len(table_slice.partition_dimensions) > 0:
            query = (
                f"SELECT {col_str} FROM"
                f" `{table_slice.database}.{table_slice.schema}.{table_slice.table}` WHERE\n"
            )
            return query + _partition_where_clause(table_slice.partition_dimensions)
        else:
            return f"""SELECT {col_str} FROM `{table_slice.database}.{table_slice.schema}.{table_slice.table}`"""

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        connection.query(f"CREATE SCHEMA IF NOT EXISTS {table_slice.schema}").result()

    @staticmethod
    @contextmanager
    def connect(context, _):
        conn = bigquery.Client(
            project=context.resource_config.get("project"),
            location=context.resource_config.get("location"),
        )

        yield conn


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    if table_slice.partition_dimensions and len(table_slice.partition_dimensions) > 0:
        query = (
            f"DELETE FROM `{table_slice.database}.{table_slice.schema}.{table_slice.table}` WHERE\n"
        )
        return query + _partition_where_clause(table_slice.partition_dimensions)
    else:
        return f"TRUNCATE TABLE `{table_slice.database}.{table_slice.schema}.{table_slice.table}`"


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND\n".join(
        (
            _time_window_where_clause(partition_dimension)
            if isinstance(partition_dimension.partitions, TimeWindow)
            else _static_where_clause(partition_dimension)
        )
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast(TimeWindow, table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    return f"""{table_partition.partition_expr} in ({partitions})"""
