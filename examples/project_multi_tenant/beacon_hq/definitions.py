from __future__ import annotations

import dagster as dg

from beacon_hq.assets import reports
from beacon_hq.jobs import beacon_executive_briefing_job, beacon_reporting_inputs_job
from beacon_hq.resources import get_resources
from beacon_hq.sensors import beacon_after_upstream_success_sensor


defs = dg.Definitions(
    assets=dg.load_assets_from_modules(
        [reports],
        key_prefix=["beacon_hq"],
    ),
    jobs=[
        beacon_reporting_inputs_job,
        beacon_executive_briefing_job,
    ],
    resources=get_resources(),
    sensors=[beacon_after_upstream_success_sensor],
)
