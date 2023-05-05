import copy
from typing import Sequence

from dagster import (
    AssetsDefinition,
    PartitionKeyRange,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    run,
    run_request,
    single_asset_run,
)
from .freshness_policy_scenarios import overlapping_freshness_inf
from .partition_scenarios import (
    hourly_partitions_def,
    hourly_to_daily_partitions,
    two_assets_in_sequence_one_partition,
)


def with_auto_materialize_policy(
    assets_defs: Sequence[AssetsDefinition], auto_materialize_policy: AutoMaterializePolicy
) -> Sequence[AssetsDefinition]:
    """Note: this should be implemented in core dagster at some point, and this implementation is
    a lazy hack.
    """
    ret = []
    for assets_def in assets_defs:
        new_assets_def = copy.copy(assets_def)
        new_assets_def._auto_materialize_policies_by_key = {  # noqa: SLF001
            asset_key: auto_materialize_policy for asset_key in new_assets_def.asset_keys
        }
        ret.append(new_assets_def)
    return ret


# auto materialization policies
auto_materialize_policy_scenarios = {
    "auto_materialize_policy_eager_with_freshness_policies": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            overlapping_freshness_inf, AutoMaterializePolicy.eager()
        ),
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[
            run_request(asset_keys=["asset2", "asset3", "asset4", "asset5", "asset6"])
        ],
    ),
    "auto_materialize_policy_lazy_with_freshness_policies": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            overlapping_freshness_inf, AutoMaterializePolicy.lazy()
        ),
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[],
    ),
    "auto_materialize_policy_with_default_scope_hourly_to_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            # with default scope, only the last partition is materialized
            run_request(
                asset_keys=["hourly"],
                partition_key=hourly_partitions_def.get_last_partition_key(
                    current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4)
                ),
            )
        ],
    ),
    "auto_materialize_policy_with_custom_scope_hourly_to_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy(
                on_missing=True,
                for_freshness=True,
                on_new_parent_data=True,
                time_window_partition_scope_minutes=24 * 2 * 60,
            ),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-04:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "auto_materialize_policy_with_custom_scope_hourly_to_daily_partitions_never_materialized2": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy(
                on_missing=True,
                for_freshness=True,
                on_new_parent_data=False,
                time_window_partition_scope_minutes=24 * 2 * 60,
            ),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-04:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "auto_materialize_policy_lazy_parent_rematerialized_one_partition": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            two_assets_in_sequence_one_partition,
            AutoMaterializePolicy.lazy(),
        ),
        unevaluated_runs=[
            run(["asset1", "asset2"], partition_key="a"),
            single_asset_run(asset_key="asset1", partition_key="a"),
        ],
        # no need to rematerialize as this is a lazy policy
        expected_run_requests=[],
    ),
}
