from dagster import SchedulingCondition, asset
from dagster._core.definitions.auto_materialize_sensor_definition import (
    DeclarativeSchedulingZone,
)
from dagster._core.definitions.definitions_class import Definitions


@asset
def different_asset() -> None: ...


@asset
def upstream_lijksdkfjsd() -> None: ...


@asset(
    deps=[upstream_lijksdkfjsd],
    auto_materialize_policy=SchedulingCondition.eager_with_rate_limit().as_auto_materialize_policy(),
)
def downstream_lskjdflksjd() -> None: ...


defs = Definitions(
    assets=[different_asset, upstream_lijksdkfjsd, downstream_lskjdflksjd],
    sensors=[
        DeclarativeSchedulingZone(
            name="sensor_zone_one_ksjdkfd",
            asset_selection=[upstream_lijksdkfjsd, downstream_lskjdflksjd],
        ),
        DeclarativeSchedulingZone(
            name="sensor_zone_two_kjsdkfjd", asset_selection=[different_asset]
        ),
    ],
)
