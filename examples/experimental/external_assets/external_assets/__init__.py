from dagster import (
    Definitions,
)

from .external_assets import external_asset_check, external_asset_defs
from .pipes import cdn_asset_job, cdn_logs_sensor, scrubbed_cdn_logs

defs = Definitions(
    assets=[*external_asset_defs, scrubbed_cdn_logs],
    asset_checks=[external_asset_check],
    sensors=[cdn_logs_sensor],
    jobs=[cdn_asset_job],
)
