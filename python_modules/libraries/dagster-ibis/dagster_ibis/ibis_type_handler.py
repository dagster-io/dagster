from collections.abc import Sequence

import ibis
import ibis.expr.types as ir
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice

from dagster_ibis.io_manager import IbisClient


class IbisTypeHandler(DbTypeHandler[ir.Table]):
    """Stores and loads Ibis Tables in a database.

    Example:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_ibis import IbisIOManager
            import ibis
            import ibis.expr.types as ir
            import pandas as pd

            @asset
            def my_table() -> ir.Table:  # the name of the asset will be the table name
                # Create an Ibis table
                df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
                return ibis.memtable(df)

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": IbisIOManager(
                        backend="duckdb",
                        database="my_db.duckdb",
                        schema="my_schema"
                    )
                }
            )
    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: ir.Table, connection
    ) -> None:
        """Stores the Ibis table in the database."""
        if table_slice.table not in connection.list_tables(database=table_slice.schema):
            connection.create_table(table_slice.table, obj, database=table_slice.schema)
        else:
            connection.insert(table_slice.table, obj, database=table_slice.schema)

        count = connection.execute(obj.count())
        context.add_output_metadata(
            {
                # output object may be a slice/partition, so we output different metadata keys based on
                # whether this output represents an entire table or just a slice/partition
                **(
                    TableMetadataSet(partition_row_count=count)
                    if context.has_partition_key
                    else TableMetadataSet(row_count=count)
                ),
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in obj.schema().items()
                        ]
                    ),
                ),
            }
        )

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> ir.Table:
        """Loads the input as an Ibis Table."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            # Return an empty table with the appropriate schema if we're asking for an empty partition
            # This behavior matches other I/O managers
            # The exact implementation depends on the backend, but memtable is a reasonable default
            return ibis.memtable([])

        return IbisClient.get_select_expr(
            connection.table(table_slice.table, database=table_slice.schema), table_slice
        )

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [ir.Table]
