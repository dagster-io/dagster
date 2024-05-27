from dagster import Definitions, asset
from dagster._core.definitions.automation.automation import (
    Automation,
)


@asset
def asset_one() -> None: ...


@asset
def asset_two() -> None: ...


defs = Definitions(
    automations=[
        Automation.cron(
            name="daily_job", targets=[asset_one, asset_two], cron_schedule="0 0 * * *"
        )
    ]
)
