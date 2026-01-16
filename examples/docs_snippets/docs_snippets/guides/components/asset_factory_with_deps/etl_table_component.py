from collections.abc import Sequence

from dagster_snowflake import SnowflakeResource

import dagster as dg


# start_etl_table_model
class EtlTable(dg.Model):
    name: str
    deps: list[str] = []
    query: str


# end_etl_table_model


# start_etl_table_component
class EtlTableFactory(dg.Component, dg.Model, dg.Resolvable):
    etl_tables: list[EtlTable]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        assets = []

        for table in self.etl_tables:

            def create_etl_asset(table_config: EtlTable):
                @dg.asset(name=table_config.name, deps=table_config.deps)
                def etl_table(snowflake: SnowflakeResource):
                    with snowflake.get_connection() as conn:
                        conn.cursor.execute(table_config.query)

                return etl_table

            assets.append(create_etl_asset(table))

        return dg.Definitions(assets=assets)


# end_etl_table_component
