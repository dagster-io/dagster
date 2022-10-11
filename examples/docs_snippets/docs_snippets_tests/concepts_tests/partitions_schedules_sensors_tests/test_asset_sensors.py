from dagster import (
    AssetKey,
    DagsterInstance,
    RunRequest,
    asset,
    build_multi_asset_sensor_context,
    materialize,
    repository,
)
from dagster._core.test_utils import instance_for_test
from docs_snippets.concepts.partitions_schedules_sensors.sensors.asset_sensors import (
    asset_a_and_b_sensor,
    asset_a_and_b_sensor_with_skip_reason,
    downstream_daily_asset,
    downstream_weekly_asset,
    trigger_daily_asset_if_both_upstream_partitions_materialized,
    trigger_daily_asset_when_any_upstream_partitions_have_new_materializations,
    trigger_weekly_asset_from_daily_asset,
    upstream_daily_1,
    upstream_daily_2,
)


def test_asset_sensors():
    @asset
    def asset_a():
        return 1

    @asset
    def asset_b():
        return 2

    @asset
    def asset_c():
        return 3

    @repository
    def my_repo():
        return [asset_a, asset_b, asset_c]

    instance = DagsterInstance.ephemeral()
    materialize([asset_a, asset_b], instance=instance)
    ctx = build_multi_asset_sensor_context(
        asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
        instance=instance,
        repository_def=my_repo,
    )
    assert isinstance(list(asset_a_and_b_sensor(ctx))[0], RunRequest)

    for _ in range(5):
        materialize([asset_c], instance=instance)

    ctx = build_multi_asset_sensor_context(
        asset_keys=[AssetKey("asset_c")],
        instance=instance,
        repository_def=my_repo,
    )
    assert list(asset_a_and_b_sensor_with_skip_reason(ctx))[0].run_config == {}


@repository
def my_repo():
    return [
        upstream_daily_1,
        upstream_daily_2,
        trigger_daily_asset_if_both_upstream_partitions_materialized,
        trigger_daily_asset_when_any_upstream_partitions_have_new_materializations,
        downstream_daily_asset,
        downstream_weekly_asset,
    ]


def test_multi_asset_sensor_AND():
    with instance_for_test() as instance:
        materialize(
            [upstream_daily_1, upstream_daily_2],
            instance=instance,
            partition_key="2022-08-01",
        )
        and_ctx = build_multi_asset_sensor_context(
            asset_keys=[AssetKey("upstream_daily_1"), AssetKey("upstream_daily_2")],
            instance=instance,
            repository_def=my_repo,
        )
        run_requests = list(
            trigger_daily_asset_if_both_upstream_partitions_materialized(and_ctx)
        )
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-01"

        materialize([upstream_daily_1], instance=instance, partition_key="2022-08-02")
        assert (
            len(
                list(
                    trigger_daily_asset_if_both_upstream_partitions_materialized(
                        and_ctx
                    )
                )
            )
            == 0
        )

        materialize([upstream_daily_2], instance=instance, partition_key="2022-08-02")
        run_requests = list(
            trigger_daily_asset_if_both_upstream_partitions_materialized(and_ctx)
        )
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-02"


def test_multi_asset_sensor_OR():
    with instance_for_test() as instance:
        materialize(
            [upstream_daily_1, upstream_daily_2],
            instance=instance,
            partition_key="2022-08-01",
        )
        or_ctx = build_multi_asset_sensor_context(
            asset_keys=[AssetKey("upstream_daily_1"), AssetKey("upstream_daily_2")],
            instance=instance,
            repository_def=my_repo,
        )
        run_requests = list(
            trigger_daily_asset_when_any_upstream_partitions_have_new_materializations(
                or_ctx
            )
        )
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-01"

        materialize([upstream_daily_1], instance=instance, partition_key="2022-08-01")
        run_requests = list(
            trigger_daily_asset_when_any_upstream_partitions_have_new_materializations(
                or_ctx
            )
        )
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-01"


def test_multi_asset_sensor_weekly_from_daily():
    with instance_for_test() as instance:
        for date in [
            "2022-08-14",
            "2022-08-15",
            "2022-08-16",
            "2022-08-17",
            "2022-08-18",
            "2022-08-19",
            "2022-08-20",
        ]:
            materialize([upstream_daily_1], instance=instance, partition_key=date)
        ctx = build_multi_asset_sensor_context(
            asset_keys=[AssetKey("upstream_daily_1")],
            instance=instance,
            repository_def=my_repo,
        )
        run_requests = list(trigger_weekly_asset_from_daily_asset(ctx))
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-14"

        materialize([upstream_daily_1], instance=instance, partition_key="2022-08-21")
        run_requests = list(trigger_weekly_asset_from_daily_asset(ctx))
        assert len(run_requests) == 0

        materialize([upstream_daily_1], instance=instance, partition_key="2022-08-20")
        run_requests = list(trigger_weekly_asset_from_daily_asset(ctx))
        assert len(run_requests) == 1
        assert run_requests[0].tags["dagster/partition"] == "2022-08-14"
