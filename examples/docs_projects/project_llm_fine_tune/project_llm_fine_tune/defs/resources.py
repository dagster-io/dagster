import dagster as dg
from dagster_duckdb import DuckDBResource
from dagster_openai import OpenAIResource

defs = dg.Definitions(
    resources={
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
        "duckdb_resource": DuckDBResource(database="data/data.duckdb"),
    },
)
