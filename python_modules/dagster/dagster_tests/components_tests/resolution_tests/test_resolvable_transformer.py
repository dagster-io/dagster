import datetime
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

import dagster as dg
from dagster._core.definitions.freshness import InternalFreshnessPolicy, TimeWindowFreshnessPolicy
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetSpecKwargs, resolve_asset_spec


def test_asset_spec():
    model = AssetSpecKwargs.model()(
        key="asset_key",
    )

    asset_spec = resolve_asset_spec(
        model=model,
        context=ResolutionContext.default(),
    )

    assert asset_spec.key == dg.AssetKey("asset_key")

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
        freshness_policy="{{sample_freshness_policy}}",
    )

    kitchen_sink_spec = resolve_asset_spec(
        model=kitchen_sink_model,
        context=ResolutionContext.default().with_scope(
            sample_freshness_policy=InternalFreshnessPolicy.time_window(
                fail_window=datetime.timedelta(minutes=10),
                warn_window=datetime.timedelta(minutes=5),
            )
        ),
    )

    assert kitchen_sink_spec.key == dg.AssetKey("kitchen_sink")
    assert kitchen_sink_spec.deps == [
        dg.AssetDep(asset=dg.AssetKey(["upstream"])),
        dg.AssetDep(asset=dg.AssetKey(["prefixed", "upstream"])),
    ]
    assert kitchen_sink_spec.description == "A kitchen sink"
    assert kitchen_sink_spec.metadata == {"key": "value"}
    assert kitchen_sink_spec.group_name == "group_name"
    assert kitchen_sink_spec.skippable is False
    assert kitchen_sink_spec.code_version == "code_version"
    assert kitchen_sink_spec.owners == ["owner@owner.com"]
    assert kitchen_sink_spec.tags == {"tag": "value", "dagster/kind/kind": ""}
    assert kitchen_sink_spec.kinds == {"kind"}
    assert isinstance(kitchen_sink_spec.automation_condition, dg.AutomationCondition)
    assert kitchen_sink_spec.automation_condition.get_label() == "eager"
    partitions_def = kitchen_sink_spec.partitions_def
    assert isinstance(partitions_def, dg.DailyPartitionsDefinition)
    assert partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, tzinfo=datetime.timezone(datetime.timedelta(hours=-5))
    )
    assert partitions_def.timezone == "America/New_York"
    assert partitions_def.minute_offset == 0

    assert kitchen_sink_spec.freshness_policy == TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=datetime.timedelta(minutes=10),
        warn_window=datetime.timedelta(minutes=5),
    )


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
    assert isinstance(spec.partitions_def, dg.DailyPartitionsDefinition)
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
    assert isinstance(spec.partitions_def, dg.HourlyPartitionsDefinition)
    assert spec.partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, hour=0, tzinfo=datetime.timezone.utc
    )
    assert spec.partitions_def.end == datetime.datetime(
        year=2021, month=1, day=1, hour=2, tzinfo=datetime.timezone.utc
    )


def test_asset_spec_weekly_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "weekly",
            "start_date": "2021-01-01",
            "timezone": "UTC",
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, dg.WeeklyPartitionsDefinition)
    assert spec.partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, tzinfo=datetime.timezone.utc
    )


def test_asset_spec_time_window_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "time_window",
            "start_date": "2021-01-01",
            "timezone": "UTC",
            "fmt": "%Y-%m-%d",
            "cron_schedule": "0 11/2 * * *",
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, dg.TimeWindowPartitionsDefinition)
    assert spec.partitions_def.start == datetime.datetime(
        year=2021, month=1, day=1, tzinfo=datetime.timezone.utc
    )
    assert spec.partitions_def.timezone == "UTC"
    assert spec.partitions_def.cron_schedule == "0 11/2 * * *"


def test_asset_spec_static_partitions_def():
    model = AssetSpecKwargs.model()(
        key="asset_key",
        partitions_def={
            "type": "static",
            "partition_keys": ["a", "b", "c"],
        },
    )

    spec = resolve_asset_spec(model=model, context=ResolutionContext.default())
    assert isinstance(spec.partitions_def, dg.StaticPartitionsDefinition)
    assert spec.partitions_def.get_partition_keys() == ["a", "b", "c"]


def test_resolved_asset_spec() -> None:
    @dataclass
    class SomeObject(dg.Resolvable):
        spec: dg.ResolvedAssetSpec
        maybe_spec: Optional[dg.ResolvedAssetSpec]
        specs: Sequence[dg.ResolvedAssetSpec]
        maybe_specs: Optional[Sequence[dg.ResolvedAssetSpec]]

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

    assert some_object.specs == [dg.AssetSpec(key="asset1"), dg.AssetSpec(key="asset2")]
