import dagster as dg
from dagster_openai import OpenAIResource
from dagster_duckdb import DuckDBResource

import project_llm_fine_fune.assets as assets


all_assets = dg.load_assets_from_modules([assets])
external_assets = [assets.goodreads]

defs = dg.Definitions(
    assets=all_assets + external_assets,
    asset_checks=[
        assets.training_file_format_check,
        assets.validation_file_format_check,
        assets.fine_tuned_model_accuracy,
    ],
    resources={
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
        "duckdb_resource": DuckDBResource(database="data/data.duckdb"),
    },
)
