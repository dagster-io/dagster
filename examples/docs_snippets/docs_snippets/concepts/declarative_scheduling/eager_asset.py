from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    Scheduling,
)


@asset()
def upstream() -> None: ...


@asset(deps=[upstream], scheduling=Scheduling.eager())
def downstream() -> None: ...
