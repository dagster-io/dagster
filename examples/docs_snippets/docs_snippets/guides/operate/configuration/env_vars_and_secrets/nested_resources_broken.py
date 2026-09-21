from dagster_duckdb import DuckDBResource

import dagster as dg

# highlight-start
duckdb_resource = DuckDBResource(database=dg.EnvVar("DUCKDB_DATABASE"))
# highlight-end


class DynamicDatabaseResource(dg.ConfigurableResource):
    env: str

    def get_resource(self) -> DuckDBResource:
        return duckdb_resource


@dg.definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"database": DynamicDatabaseResource(env="development")},
    )
