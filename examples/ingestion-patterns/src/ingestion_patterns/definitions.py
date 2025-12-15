import dagster as dg
from dagster_duckdb import DuckDBResource

import ingestion_patterns.defs as definitions

defs = dg.Definitions.merge(
    dg.components.load_defs(definitions),
    dg.Definitions(
        resources={
            "duckdb": DuckDBResource(database="ingestion_patterns.duckdb"),
        },
    ),
)
