from typing import Iterable, Mapping, Optional, Sequence

from dagster import Definitions, asset
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.declarative_scheduling.ds_sensor import DSSensorDefinition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.instance import DagsterInstance
from dagster._daemon.asset_daemon import (
    asset_daemon_cursor_from_instigator_serialized_cursor,
    asset_daemon_cursor_to_instigator_serialized_cursor,
)


def ds_asset(
    *,
    deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    description: Optional[str] = None,
    metadata: Optional[ArbitraryMetadataMapping] = None,
    group_name: Optional[str] = None,
    code_version: Optional[str] = None,
    key: Optional[CoercibleToAssetKey] = None,
    scheduling: Optional[SchedulingCondition] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    owners: Optional[Sequence[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
):
    return asset(
        key=key,
        deps=deps,
        description=description,
        metadata=metadata,
        group_name=group_name,
        code_version=code_version,
        auto_materialize_policy=(scheduling.as_auto_materialize_policy() if scheduling else None),
        check_specs=check_specs,
        owners=owners,
        tags=tags,
    )


def pulse_ds_sensor(
    sensor_def: DSSensorDefinition,
    instance: DagsterInstance,
    defs: Definitions,
    asset_daemon_cursor: AssetDaemonCursor,
) -> AssetDaemonCursor:
    repository_def = defs.get_repository_def()
    sensor_context = build_sensor_context(
        instance=instance,
        repository_def=repository_def,
        cursor=asset_daemon_cursor_to_instigator_serialized_cursor(asset_daemon_cursor),
    )
    result = sensor_def(sensor_context)

    assert isinstance(result, SensorResult)

    return asset_daemon_cursor_from_instigator_serialized_cursor(
        serialized_cursor=result.cursor, asset_graph=repository_def.asset_graph
    )


def test_basic_ds_sensor() -> None:
    @ds_asset(scheduling=SchedulingCondition.eager_with_rate_limit())
    def an_asset() -> None: ...

    sensor_def = DSSensorDefinition(
        name="test_sensor",
        asset_selection="*",
    )

    defs = Definitions(assets=[an_asset], sensors=[sensor_def])

    instance = DagsterInstance.ephemeral()

    next_cursor = pulse_ds_sensor(
        sensor_def=sensor_def,
        instance=instance,
        defs=defs,
        asset_daemon_cursor=AssetDaemonCursor.empty(),
    )

    assert isinstance(next_cursor, AssetDaemonCursor)
