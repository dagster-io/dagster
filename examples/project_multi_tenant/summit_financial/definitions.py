from __future__ import annotations

import dagster as dg

from summit_financial.assets import bronze, gold, silver
from summit_financial.jobs import (
    summit_context_engineering_job,
    summit_raw_data_job,
    summit_risk_scoring_job,
)
from summit_financial.schedules import summit_daily_refresh_schedule
from shared.io_managers import make_duckdb_io_manager
from shared.resources import RiskReviewer, build_llm_resource


defs = dg.Definitions(
    assets=dg.load_assets_from_modules(
        [bronze, silver, gold],
        key_prefix=["summit_financial"],
    ),
    jobs=[
        summit_raw_data_job,
        summit_context_engineering_job,
        summit_risk_scoring_job,
    ],
    resources={
        "llm": build_llm_resource(
            RiskReviewer,
            model_env_var="SUMMIT_FINANCIAL_MODEL",
            legacy_model_env_var="TENANT_BETA_MODEL",
            default_model_name="qwen2.5:1.5b",
            runtime_dependency_package="risk_reviewer_runtime",
        ),
        "io_manager": make_duckdb_io_manager("summit_financial"),
    },
    schedules=[summit_daily_refresh_schedule],
)
