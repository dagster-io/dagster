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

            @dg.asset(
                name=etl.table,
            )
            def _table(duckdb: DuckDBResource):
                with duckdb.get_connection() as conn:
                    conn.execute(
                        f"""
                        create or replace table {etl.table} as (
                            select * from read_csv_auto('{etl.url_path}')
                        )
                        """
                    )

            _etl_assets.append(_table)

        return dg.Definitions(
            assets=_etl_assets,
            resources={"duckdb": DuckDBResource(database=self.duckdb_database)},
        )


# end_tutorial_component
