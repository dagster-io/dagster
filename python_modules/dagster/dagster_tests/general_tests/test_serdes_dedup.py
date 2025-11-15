import dagster as dg
from dagster import DagsterInstance
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes
from dagster_shared.serdes.serdes import deserialize_value_with_dedup, serialize_value_with_dedup


@whitelist_for_serdes
@record
class Inner:
    number: float


@whitelist_for_serdes
@record
class Foo:
    name: str
    value: int
    inner: Inner


@whitelist_for_serdes
@record
class Bar:
    name: str
    single: Foo
    multiple: list[Foo]


def test_dedup():
    # same object, different ids
    f1 = Foo(name="f1", value=1, inner=Inner(number=1.0))
    f1_same = Foo(name="f1", value=1, inner=Inner(number=1.0))

    f2 = Foo(name="f2", value=2, inner=Inner(number=2.0))

    bar = Bar(name="bar", single=f1, multiple=[f1, f1, f1_same, f1_same, f2])

    serialized = serialize_value_with_dedup(bar)
    assert "__dedup_mapping__" in serialized
    assert "__dedup_ref__" in serialized
    deserialized = deserialize_value_with_dedup(serialized, as_type=Bar)
    assert deserialized == bar


def test_cursor():
    daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(partitions_def=daily_partitions)
    def upstream_1() -> None: ...

    @dg.asset(partitions_def=daily_partitions)
    def upstream_2() -> None: ...

    @dg.asset(partitions_def=daily_partitions)
    def upstream_3() -> None: ...

    @dg.asset(partitions_def=daily_partitions)
    def upstream_4() -> None: ...

    @dg.asset(partitions_def=daily_partitions)
    def upstream_5() -> None: ...

    @dg.asset(
        deps=[upstream_1, upstream_2, upstream_3, upstream_4, upstream_5],
        automation_condition=dg.AutomationCondition.on_cron(cron_schedule="0 * * * *"),
    )
    def downstream() -> None: ...

    defs = dg.Definitions(
        assets=[upstream_1, upstream_2, upstream_3, upstream_4, upstream_5, downstream]
    )
    instance = DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    cursor = result.cursor
    assert isinstance(cursor, AssetDaemonCursor)

    serialized = serialize_value_with_dedup(cursor)
    assert "__dedup_mapping__" in serialized
    assert "__dedup_ref__" in serialized
    deserialized = deserialize_value_with_dedup(serialized, as_type=AssetDaemonCursor)
    assert deserialized == cursor
