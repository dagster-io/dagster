from collections.abc import Mapping, Sequence
from typing import Optional

import ibis
import ibis.expr.types as ir
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice


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
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the Ibis table in the database."""
        try:
            # Create or replace the table in the database
            qualified_name = f"{table_slice.schema}.{table_slice.table}"

            # Check if we're dealing with a partitioned output
            if table_slice.partition_dimensions:
                # For partitioned data, we need to first check if the table exists
                # If not, create it with the schema from our expression
                if table_slice.table not in connection.list_tables(database=table_slice.schema):
                    # Create the table
                    connection.create_table(table_slice.table, obj, database=table_slice.schema)

                # For partitioned tables, we'll insert data
                context.log.info(f"Writing partitioned data to {qualified_name}")

                # Execute the insert - how this is done depends on the specific backend
                # Some backends support direct insert, others might need temporary tables
                if hasattr(connection, "insert"):
                    connection.insert(qualified_name, obj)
                else:
                    # For backends without direct insert support
                    # Create a temp view and then insert from it
                    temp_name = f"_temp_{table_slice.table}"
                    obj.create_view(temp_name, temporary=True)
                    connection.sql(f"INSERT INTO {qualified_name} SELECT * FROM {temp_name}")
            else:
                # For full table replacement, we can create a table directly
                context.log.info(f"Creating/replacing table {qualified_name}")
                connection.create_table(
                    table_slice.table, obj, database=table_slice.schema, overwrite=True
                )

            # Get metadata about the table
            try:
                # Try to get row count
                count_expr = ibis.sql(f"SELECT COUNT(*) FROM {qualified_name}")
                row_count = connection.execute(count_expr).iloc[0, 0]

                # Get schema information
                schema_info = []
                for col_name, col_type in zip(obj.columns, obj.dtypes):
                    schema_info.append(TableColumn(name=col_name, type=str(col_type)))

                # Return metadata
                return {
                    # Output object may be a slice/partition, so we output different metadata keys
                    **(
                        TableMetadataSet(partition_row_count=row_count)
                        if context.has_partition_key
                        else TableMetadataSet(row_count=row_count)
                    ),
                    "table_schema": MetadataValue.table_schema(TableSchema(columns=schema_info)),
                }
            except Exception as e:
                context.log.warning(f"Could not gather table metadata: {e!s}")
                return {}

        except Exception as e:
            context.log.error(
                f"Error writing table to {table_slice.schema}.{table_slice.table}: {e!s}"
            )
            raise

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> ir.Table:
        """Loads the input as an Ibis Table."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            # Return an empty table with the appropriate schema if we're asking for an empty partition
            # This behavior matches other I/O managers
            # The exact implementation depends on the backend, but memtable is a reasonable default
            return ibis.memtable([])

        # Create a reference to the table in the database
        qualified_name = f"{table_slice.schema}.{table_slice.table}"

        # If we're only selecting specific columns
        if table_slice.columns:
            table_ref = connection.table(table_slice.table, database=table_slice.schema)
            cols = [table_ref[col] for col in table_slice.columns]
            expr = table_ref.select(cols)
        else:
            expr = connection.table(table_slice.table, database=table_slice.schema)

        # Apply partition filters if necessary
        if table_slice.partition_dimensions:
            # We need to create a filter expression based on partitions
            # This is a simplification and may need adjustment based on backend
            where_clause = connection.sql(
                f"SELECT * FROM {qualified_name} WHERE {_partition_where_clause(connection, table_slice.partition_dimensions)}"
            )
            expr = where_clause

        return expr

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [ir.Table]


def _partition_where_clause(connection, partition_dimensions):
    """Convert partition dimensions to a SQL WHERE clause string."""
    # This would need to be implemented to match the DbClient partition handling
    # For now, this is a placeholder
    clauses = []

    for dimension in partition_dimensions:
        if hasattr(dimension.partitions, "start") and hasattr(dimension.partitions, "end"):
            # Time window partition
            start_str = dimension.partitions.start.strftime("%Y-%m-%d %H:%M:%S")
            end_str = dimension.partitions.end.strftime("%Y-%m-%d %H:%M:%S")
            clauses.append(
                f"{dimension.partition_expr} >= '{start_str}' AND {dimension.partition_expr} < '{end_str}'"
            )
        else:
            # Static partition
            partitions_list = ", ".join(f"'{p}'" for p in dimension.partitions)
            clauses.append(f"{dimension.partition_expr} IN ({partitions_list})")

    return " AND ".join(clauses)
