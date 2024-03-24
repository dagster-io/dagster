from dagster import (
    Field,
    IOManagerDefinition,
    OutputContext,
    StringSource,
    io_manager,
    InputContext,
)

from abc import ABC, abstractmethod
from typing import Dict, Generic, Mapping, Optional, Type, TypeVar, Any, Sequence
from upath import UPath

import dagster._check as check
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.upath_io_manager import UPathIOManager

T = TypeVar("T")


class FsTypeHandler(ABC, Generic[T]):
    @abstractmethod
    def handle_output(
        self, context: OutputContext, obj: T, path: UPath
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""

    @abstractmethod
    def load_input(self, context: InputContext, path: UPath) -> T:
        """Loads the contents of the given table in the given schema."""

    @property
    @abstractmethod
    def supported_types(self) -> Sequence[Type]:
        pass


def build_s3_parquet_io_manager(type_handlers: Sequence[FsTypeHandler]) -> IOManagerDefinition:
    """
    Builds an IO manager definition that reads inputs from and writes outputs to S3 as Parquet files.
    # TODO - update doc string
    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            DuckDB tables and an in-memory type - e.g. a Pandas DataFrame.
    Returns:
        IOManagerDefinition
    Examples:
        .. code-block:: python
            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler
            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...
            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])
            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": duckdb_io_manager.configured({"database": "my_db.duckdb"})}
                )
    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the IO Manager. For assets, the schema will be determined from the asset key. For ops, the schema can be
    specified by including a "schema" entry in output metadata. If none of these is provided, the schema will
    default to "public".
    .. code-block:: python
        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...
    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.
    .. code-block:: python
        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame):
            # my_table will just contain the data from column "a"
            ...
    """

    @io_manager(
        config_schema={
            "bucket": Field(
                StringSource,
                description="Name of the bucket to use.",
            ),
            "prefix": Field(StringSource),  # elementl-dev - sort of like the database?
        },
        required_resource_keys="s3",
    )
    def s3_parquet_io_manager(init_context):
        """IO Manager for storing outputs in a S3 as Parquet files
        # TODO update doc string
        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
        table of the name of the output.
        """
        return S3ParquetIOManager(
            type_handlers=type_handlers,
            bucket=init_context.resource_config["bucket"],
            prefix=init_context.resource_config.get("prefix"),
        )

    return s3_parquet_io_manager


class S3ParquetIOManager(UPathIOManager):
    extension: str = ".parquet"

    def __init__(
        self,
        *,
        type_handlers: Sequence[FsTypeHandler],
        bucket: str,
        prefix: Optional[str] = None,
    ):
        self._handlers_by_type: Dict[Optional[Type], FsTypeHandler] = {}
        for type_handler in type_handlers:
            for handled_type in type_handler.supported_types:
                check.invariant(
                    handled_type not in self._handlers_by_type,
                    f"S3ParquetIOManager provided with two handlers for the same type. "
                    f"Type: '{handled_type}'. Handler classes: '{type(type_handler)}' and "
                    f"'{type(self._handlers_by_type.get(handled_type))}'.",
                )

                self._handlers_by_type[handled_type] = type_handler
        self._bucket = bucket
        self._prefix = prefix
        self._upath = UPath(f"s3://{bucket}{'/' + self._prefix if self._prefix else ''}")

        super().__init__(base_path=self._upath)

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):

        if obj is not None:
            obj_type = type(obj)
            check.invariant(
                obj_type in self._handlers_by_type,
                f"S3ParquetIOManager does not have a handler for type '{obj_type}'. Has handlers "
                f"for types '{', '.join([str(handler_type) for handler_type in self._handlers_by_type.keys()])}'",
            )

            handler_metadata = (
                self._handlers_by_type[obj_type].handle_output(context, obj, path) or {}
            )
        else:
            check.invariant(
                context.dagster_type.is_nothing,
                "Unexpected 'None' output value. If a 'None' value is intentional, set the output type to None.",
            )
            # if obj is None, assume that I/O was handled in the op body
            handler_metadata = {}

        context.add_output_metadata({**handler_metadata, "Path": path})

    def load_from_path(self, context: InputContext, path: UPath) -> object:
        obj_type = context.dagster_type.typing_type
        check.invariant(
            obj_type in self._handlers_by_type,
            f"S3ParquetIOManager does not have a handler for type '{obj_type}'. Has handlers "
            f"for types '{', '.join([str(handler_type) for handler_type in self._handlers_by_type.keys()])}'",
        )
        return self._handlers_by_type[obj_type].load_input(context, path)
