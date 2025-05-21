from collections.abc import Sequence

import ibis
import pandas as pd
from dagster import InputContext, OutputContext
from dagster._core.storage.db_io_manager import TableSlice

from dagster_ibis.ibis_type_handler import IbisTypeHandler


class PandasTypeHandler(IbisTypeHandler):
    """Stores and loads pandas DataFrames in a database.

    Example:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_ibis import IbisIOManager
            import pandas as pd

            @asset
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                # Create a pandas DataFrame
                df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
                return df

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
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection
    ) -> None:
        """Stores the pandas DataFrame in the database."""
        super().handle_output(context, table_slice, ibis.memtable(obj), connection)

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pd.DataFrame:
        """Loads the input as a pandas DataFrame."""
        return super().load_input(context, table_slice, connection).to_pandas()

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [pd.DataFrame]
