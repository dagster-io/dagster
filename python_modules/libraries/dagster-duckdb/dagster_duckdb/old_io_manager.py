from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generic, Optional, Sequence, Type, TypeVar

import duckdb

from dagster import Field, IOManager, IOManagerDefinition, InputContext, OutputContext
from dagster import _check as check
from dagster import io_manager
from dagster._seven.temp_dir import get_system_temp_directory
from dagster._utils.backoff import backoff

T = TypeVar("T")


class DbTypeHandler(ABC, Generic[T]):
    @abstractmethod
    def handle_output(
        self, context: OutputContext, obj: T, conn: duckdb.DuckDBPyConnection, base_path: str
    ):
        """Stores the given object at the provided filepath."""

    @abstractmethod
    def load_input(self, context: InputContext, conn: duckdb.DuckDBPyConnection) -> T:
        """Loads the return of the query as the correct type."""

    @abstractmethod
    def _get_path(self, context: OutputContext, base_path: str) -> Path:
        """Creates the path where the file should be stored."""

    @property
    def supported_input_types(self) -> Sequence[Type]:
        pass

    @property
    def supported_output_types(self) -> Sequence[Type]:
        pass

    def _schema(self, context, output_context: OutputContext):
        if context.has_asset_key:
            # the schema is the second to last component of the asset key, e.g.
            # AssetKey([database, schema, tablename])
            return context.asset_key.path[-2]
        else:
            # for non-asset outputs, the schema should be specified as metadata, or will default to public
            context_metadata = output_context.metadata or {}
            return context_metadata.get("schema", "public")

    def _table(self, context, output_context: OutputContext):
        if context.has_asset_key:
            # the table is the  last component of the asset key, e.g.
            # AssetKey([database, schema, tablename])
            return context.asset_key.path[-1]
        else:
            # for non-asset outputs, the table is the output name
            return output_context.name

    def _table_path(self, context, output_context: OutputContext):
        return f"{self._schema(context, output_context)}.{self._table(context, output_context)}"


class DuckDBIOManager(IOManager):
    """Stores data in csv files and creates duckdb views over those files."""

    def __init__(self, base_path, type_handlers: Sequence[DbTypeHandler]):
        self._base_path = base_path

        self._output_handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        self._input_handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        for type_handler in type_handlers:
            for handled_output_type in type_handler.supported_output_types:
                check.invariant(
                    handled_output_type not in self._output_handlers_by_type,
                    "DuckDBIOManager provided with two handlers for the same type. "
                    f"Type: '{handled_output_type}'. Handler classes: '{type(type_handler)}' and "
                    f"'{type(self._output_handlers_by_type.get(handled_output_type))}'.",
                )

                self._output_handlers_by_type[handled_output_type] = type_handler

            for handled_input_type in type_handler.supported_input_types:
                check.invariant(
                    handled_input_type not in self._input_handlers_by_type,
                    "DuckDBIOManager provided with two handlers for the same type. "
                    f"Type: '{handled_input_type}'. Handler classes: '{type(type_handler)}' and "
                    f"'{type(self._input_handlers_by_type.get(handled_input_type))}'.",
                )

                self._input_handlers_by_type[handled_input_type] = type_handler

    def handle_output(self, context: OutputContext, obj: object):
        if obj is not None:  # if this is a dbt output, then the value will be None
            obj_type = type(obj)
            check.invariant(
                obj_type in self._output_handlers_by_type,
                f"DuckDBIOManager does not have a handler that supports outputs of type '{obj_type}'. Has handlers "
                f"for types '{', '.join([str(handler_type) for handler_type in self._output_handlers_by_type.keys()])}'",
            )
            conn = self._connect_duckdb(context).cursor()
            # type handler will store the output in duckdb
            self._output_handlers_by_type[obj_type].handle_output(
                context, obj=obj, conn=conn, base_path=self._base_path
            )
            conn.close()

    def load_input(self, context: InputContext):
        obj_type = context.dagster_type.typing_type
        check.invariant(
            obj_type in self._input_handlers_by_type,
            f"DuckDBIOManager does not have a handler that supports inputs of type '{obj_type}'. Has handlers "
            f"for types '{', '.join([str(handler_type) for handler_type in self._input_handlers_by_type.keys()])}'",
        )

        check.invariant(
            not context.has_asset_partitions, "DuckDBIOManager can't load partitioned inputs"
        )

        conn = self._connect_duckdb(context).cursor()
        ret = self._input_handlers_by_type[obj_type].load_input(context, conn=conn)
        conn.close()
        return ret

    def _connect_duckdb(self, context):
        return backoff(
            fn=duckdb.connect,
            retry_on=(RuntimeError, duckdb.IOException),
            kwargs={"database": context.resource_config["duckdb_path"], "read_only": False},
        )


def build_duckdb_io_manager(type_handlers: Sequence[DbTypeHandler]) -> IOManagerDefinition:
    """
    Builds an IO manager definition that reads inputs from and writes outputs to DuckDB.

    Note that the DuckDBIOManager cannot load partitioned assets.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            DuckDB tables and an in-memory type - e.g. a Pandas DataFrame.

    Returns:
        IOManagerDefinition

    Examples:

        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

            @job(resource_defs={'io_manager': duckdb_io_manager})
            def my_job():
                ...

    You may configure the returned IO Manager as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    base_path: path/to/store/files  # all data will be stored at this path
                    duckdb_path: path/to/database.duckdb  # path to the duckdb database
    """

    @io_manager(config_schema={"base_path": Field(str, is_required=False), "duckdb_path": str})
    def duckdb_io_manager(init_context):
        """IO Manager for storing outputs in a DuckDB database

        Supports storing and loading Pandas DataFrame objects. Converts the DataFrames to CSV and
        creates DuckDB views over the files.

        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
        table of the name of the output.
        """
        return DuckDBIOManager(
            base_path=init_context.resource_config.get("base_path", get_system_temp_directory()),
            type_handlers=type_handlers,
        )

    return duckdb_io_manager
