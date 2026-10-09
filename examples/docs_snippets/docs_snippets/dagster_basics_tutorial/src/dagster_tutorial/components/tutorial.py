# start_etl_model
import dagster as dg


class ETL(dg.Model):
    url_path: str
    table: str


# end_etl_model

# start_tutorial_component
from dagster_duckdb import DuckDBResource


class Tutorial(dg.Component, dg.Model, dg.Resolvable):
    # The interface for the component
    duckdb_database: str
    etl_steps: list[ETL]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        _etl_assets = []

        for etl in self.etl_steps:
            _etl_assets.append(_make_table_asset(etl.table, etl.url_path))

        return dg.Definitions(
            assets=_etl_assets,
            resources={"duckdb": DuckDBResource(database=self.duckdb_database)},
        )


def _make_table_asset(table: str, url_path: str):
    @dg.asset(
        name=table,
    )
    def _table(duckdb: DuckDBResource):
        with duckdb.get_connection() as conn:
            conn.execute(
                f"""
                create or replace table {table} as (
                    select * from read_csv_auto('{url_path}')
                )
                """
            )

    return _table


# end_tutorial_component
