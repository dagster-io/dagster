from dagster import Definitions, asset
from dagster._core.definitions.automation.automation import (
    Automation,
)


@asset()
def my_asset() -> None: ...


defs = Definitions(
    automations=[
        Automation.cron(name="daily_job", targets=[my_asset], cron_schedule="0 0 * * *")
    ]
)
