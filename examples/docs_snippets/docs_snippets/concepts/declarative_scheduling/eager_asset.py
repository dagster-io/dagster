from dagster import SchedulingCondition
from dagster._core.definitions.declarative_scheduling.ds_asset import ds_asset as asset


@asset()
def upstream() -> None: ...


@asset(
    deps=[upstream], scheduling_condition=SchedulingCondition.eager_with_rate_limit()
)
def downstream() -> None: ...
