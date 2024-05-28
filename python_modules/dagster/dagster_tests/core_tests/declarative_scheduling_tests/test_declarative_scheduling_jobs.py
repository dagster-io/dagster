from typing import List

from dagster import Definitions, asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.auto_materialize_sensor_definition import (
    AutoMaterializeSensorDefinition,
)
from dagster._core.definitions.declarative_scheduling.declarative_scheduling_job import (
    DeclarativeSchedulingJob,
)


def check_asset_keys(defs: Definitions, expected: List[str]):
    assert set(defs.get_asset_graph().all_asset_keys) == {
        AssetKey.from_user_string(key) for key in expected
    }


def test_initial_cron_job() -> None:
    @asset
    def my_asset() -> None: ...

    defs = Definitions(
        jobs=[
            DeclarativeSchedulingJob.cron(
                name="daily_job", targets=[my_asset], cron_schedule="0 0 * * *"
            )
        ]
    )

    # demonstrate that this is does via DS
    sensor_def = defs.get_sensor_def("daily_job")
    assert isinstance(sensor_def, AutoMaterializeSensorDefinition)
    check_asset_keys(defs, ["my_asset"])


def test_upstream_update() -> None:
    @asset(deps=[AssetKey("external_asset")])
    def triggered_asset() -> None: ...
