from __future__ import annotations

import dagster as dg

from harbor_outfitters.assets import bronze, gold, silver
from harbor_outfitters.jobs import (
    harbor_catalog_publish_job,
    harbor_context_engineering_job,
    harbor_raw_data_job,
)
from harbor_outfitters.resources import get_resources
from harbor_outfitters.schedules import harbor_daily_refresh_schedule


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
    resources=get_resources(),
    schedules=[harbor_daily_refresh_schedule],
)
