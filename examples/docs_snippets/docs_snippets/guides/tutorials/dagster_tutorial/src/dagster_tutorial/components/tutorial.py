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

        def create_asset(etl_config: ETL):
            @dg.asset(name=etl_config.table)
            def _table(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
                context.log.info(f"Building asset for table: {etl_config.table}")
                with duckdb.get_connection() as conn:
                    conn.execute(
                        f"""
                        create or replace table {etl_config.table} as (
                            select * from read_csv_auto('{etl_config.url_path}')
                        )
                        """
                    )

            return _table

        for etl in self.etl_steps:
            _etl_assets.append(create_asset(etl))

        return dg.Definitions(
            assets=_etl_assets,
            resources={"duckdb": DuckDBResource(database=self.duckdb_database)},
        )


# end_tutorial_component
