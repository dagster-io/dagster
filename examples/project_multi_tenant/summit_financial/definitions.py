from __future__ import annotations

import dagster as dg

from summit_financial.assets import bronze, gold, silver
from summit_financial.jobs import (
    summit_context_engineering_job,
    summit_raw_data_job,
    summit_risk_scoring_job,
)
from summit_financial.resources import get_resources
from summit_financial.schedules import summit_daily_refresh_schedule


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
    resources=get_resources(),
    schedules=[summit_daily_refresh_schedule],
)
