import dagster as dg
import duckdb
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_client import SQLClient


class DuckDBConnectionComponent(dg.Component, dg.Resolvable, dg.Model, SQLClient):
    """A connection component for DuckDB, for use with TemplatedSqlComponent."""

    database: str

    def connect_and_execute(self, sql: str) -> None:
        with duckdb.connect(self.database) as conn:
            conn.execute(sql)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
