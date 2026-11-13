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
            # Bug #34076: Inner factory function binds etl_step to avoid Python closure late-binding
            def create_etl_asset(etl_step: ETL):
                @dg.asset(
                    name=etl_step.table,
                )
                def _table(duckdb: DuckDBResource):
                    with duckdb.get_connection() as conn:
                        conn.execute(
                            f"""
                            create or replace table {etl_step.table} as (
                                select * from read_csv_auto('{etl_step.url_path}')
                            )
                            """
                        )

                return _table

            _etl_assets.append(create_etl_asset(etl))

        return dg.Definitions(
            assets=_etl_assets,
            resources={"duckdb": DuckDBResource(database=self.duckdb_database)},
        )


# end_tutorial_component
