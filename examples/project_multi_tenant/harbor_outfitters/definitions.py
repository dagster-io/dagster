from __future__ import annotations

import dagster as dg

from harbor_outfitters.assets import bronze, gold, silver
from harbor_outfitters.jobs import (
    harbor_catalog_publish_job,
    harbor_context_engineering_job,
    harbor_raw_data_job,
)
from harbor_outfitters.schedules import harbor_daily_refresh_schedule
from shared.io_managers import make_duckdb_io_manager
from shared.resources import CatalogCoach, build_llm_resource


defs = dg.Definitions(
    assets=dg.load_assets_from_modules(
        [bronze, silver, gold],
        key_prefix=["harbor_outfitters"],
    ),
    jobs=[
        harbor_raw_data_job,
        harbor_context_engineering_job,
        harbor_catalog_publish_job,
    ],
    resources={
        "llm": build_llm_resource(
            CatalogCoach,
            model_env_var="HARBOR_OUTFITTERS_MODEL",
            legacy_model_env_var="TENANT_ALPHA_MODEL",
            default_model_name="qwen2.5:0.5b",
            runtime_dependency_package="catalog_coach_runtime",
        ),
        "io_manager": make_duckdb_io_manager("harbor_outfitters"),
    },
    schedules=[harbor_daily_refresh_schedule],
)
