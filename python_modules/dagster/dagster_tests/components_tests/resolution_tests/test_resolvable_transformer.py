import datetime
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

from dagster import Resolvable
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import (
    AssetSpecKwargs,
    ResolvedAssetSpec,
    resolve_asset_spec,
)


def test_asset_spec():
    model = AssetSpecKwargs.model()(
        key="asset_key",
    )

    asset_spec = resolve_asset_spec(
        model=model,
        context=ResolutionContext.default(),
    )

    assert asset_spec.key == AssetKey("asset_key")

    kitchen_sink_model = AssetSpecKwargs.model()(
        key="kitchen_sink",
        deps=["upstream", "prefixed/upstream"],
        description="A kitchen sink",
        metadata={"key": "value"},
        group_name="group_name",
        skippable=False,
        code_version="code_version",
        owners=["owner@owner.com"],
        tags={"tag": "value"},
        kinds=["kind"],
        automation_condition="{{automation_condition.eager()}}",
        partitions_def={
            "type": "daily",
            "start_date": "2021-01-01",
            "timezone": "America/New_York",
            "minute_offset": 0,
        },
    )

    kitchen_sink_spec = resolve_asset_spec(
        model=kitchen_sink_model,
        context=ResolutionContext.default(),
    )

    assert kitchen_sink_spec.key == AssetKey("kitchen_sink")
    assert kitchen_sink_spec.deps == [
        AssetDep(asset=AssetKey(["upstream"])),
        AssetDep(asset=AssetKey(["prefixed", "upstream"])),
    ]
    assert kitchen_sink_spec.description == "A kitchen sink"
    assert kitchen_sink_spec.metadata == {"key": "value"}
    assert kitchen_sink_spec.group_name == "group_name"
    assert kitchen_sink_spec.skippable is False
    assert kitchen_sink_spec.code_version == "code_version"
    assert kitchen_sink_spec.owners == ["owner@owner.com"]
    assert kitchen_sink_spec.tags == {"tag": "value", "dagster/kind/kind": ""}
    assert kitchen_sink_spec.kinds == {"kind"}
    assert isinstance(kitchen_sink_spec.automation_condition, AutomationCondition)
    assert kitchen_sink_spec.automation_condition.get_label() == "eager"
    partitions_def = kitchen_sink_spec.partitions_def
    assert isinstance(partitions_def, DailyPartitionsDefinition)
    assert partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, tzinfo=datetime.timezone(datetime.timedelta(hours=-5))
    )
    assert partitions_def.timezone == "America/New_York"
    assert partitions_def.minute_offset == 0


def test_asset_spec_daily_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "daily",
            "start_date": "2021-01-01",
            "end_date": "2021-01-02",
            "minute_offset": 10,
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, DailyPartitionsDefinition)
    assert spec.partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, tzinfo=datetime.timezone.utc
    )
    assert spec.partitions_def.end == datetime.datetime(
        year=2021, month=1, day=2, tzinfo=datetime.timezone.utc
    )
    assert spec.partitions_def.minute_offset == 10


def test_asset_spec_hourly_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "hourly",
            "start_date": "2021-01-01-00:00",
            "end_date": "2021-01-01-02:00",
            "timezone": "UTC",
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, HourlyPartitionsDefinition)
    assert spec.partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, hour=0, tzinfo=datetime.timezone.utc
    )
    assert spec.partitions_def.end == datetime.datetime(
        year=2021, month=1, day=1, hour=2, tzinfo=datetime.timezone.utc
    )


def test_asset_spec_static_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "static",
            "partition_keys": ["a", "b", "c"],
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, StaticPartitionsDefinition)
    assert spec.partitions_def.get_partition_keys() == ["a", "b", "c"]


def test_resolved_asset_spec() -> None:
    @dataclass
    class SomeObject(Resolvable):
        spec: ResolvedAssetSpec
        maybe_spec: Optional[ResolvedAssetSpec]
        specs: Sequence[ResolvedAssetSpec]
        maybe_specs: Optional[Sequence[ResolvedAssetSpec]]

    some_object = SomeObject.resolve_from_model(
        context=ResolutionContext.default(),
        model=SomeObject.model()(
            spec=AssetSpecKwargs.model()(key="asset0"),
            maybe_spec=None,
            specs=[
                AssetSpecKwargs.model()(key="asset1"),
                AssetSpecKwargs.model()(key="asset2"),
            ],
            maybe_specs=None,
        ),
    )

    assert some_object.specs == [AssetSpec(key="asset1"), AssetSpec(key="asset2")]
