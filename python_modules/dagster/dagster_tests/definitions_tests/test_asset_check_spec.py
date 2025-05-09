import re

import pytest
from dagster import AssetCheckSpec, AssetKey, SourceAsset, asset
from dagster._core.instance_for_test import instance_for_test


def test_coerce_asset_key():
    assert AssetCheckSpec(asset="foo", name="check1").asset_key == AssetKey("foo")


def test_asset_def():
    @asset
    def foo(): ...

    assert AssetCheckSpec(asset=foo, name="check1").asset_key == AssetKey("foo")


def test_source_asset():
    foo = SourceAsset("foo")

    assert AssetCheckSpec(asset=foo, name="check1").asset_key == AssetKey("foo")


def test_additional_deps():
    with pytest.raises(
        ValueError,
        match=re.escape(
            'Asset check check1 for asset ["foo"] cannot have an additional dependency on asset ["foo"].'
        ),
    ):
        AssetCheckSpec(asset="foo", name="check1", additional_deps=["foo"])


def test_unserializable_metadata():
    class SomeObject: ...

    obj = SomeObject()

    assert AssetCheckSpec(asset="foo", name="check1", metadata={"foo": obj}).metadata["foo"] == obj  # pyright: ignore[reportOptionalSubscript]


def test_partitioned_asset_check() -> None:
    import dagster as dg

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition("2025-01-01"))
    def a() -> None:
        pass

    @dg.asset_check(
        asset="a",
        partitions_def=dg.DailyPartitionsDefinition("2025-01-01"),
    )
    def my_partitioned_check(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            passed=True,
        )

    defs = dg.Definitions(
        assets=[a],
        asset_checks=[my_partitioned_check],
        jobs=[dg.define_asset_job("xyz_job", selection="*")],
    )

    with instance_for_test() as instance:
        defs.get_job_def("xyz_job").execute_in_process(
            partition_key="2025-04-05",
            instance=instance,
        )
        history = instance.event_log_storage.get_asset_check_execution_history(
            my_partitioned_check.check_key, limit=20
        )
        for h in history:
            print("-------")
            print(h.status, h.event)

    assert False
