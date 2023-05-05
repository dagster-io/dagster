import copy
from typing import Sequence

from dagster import (
    AssetsDefinition,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    run,
    run_request,
)
from .freshness_policy_scenarios import diamond_freshness, overlapping_freshness_inf


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


multi_code_location_scenarios = {
    "single_code_auto_materialize_policy_eager_with_freshness_policies": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "my-location": with_auto_materialize_policy(
                overlapping_freshness_inf, AutoMaterializePolicy.eager()
            )
        },
        cursor_from=AssetReconciliationScenario(
            assets=None,
            code_locations={
                "my-location": with_auto_materialize_policy(
                    overlapping_freshness_inf, AutoMaterializePolicy.eager()
                )
            },
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[
            run_request(asset_keys=["asset2", "asset3", "asset4", "asset5", "asset6"])
        ],
    ),
    "multi_code_auto_materialize_policy_eager_with_freshness_policies": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "location-1": with_auto_materialize_policy(
                overlapping_freshness_inf[:-1], AutoMaterializePolicy.eager()
            ),
            "location-2": with_auto_materialize_policy(
                overlapping_freshness_inf[-1:], AutoMaterializePolicy.eager()
            ),
        },
        cursor_from=AssetReconciliationScenario(
            assets=None,
            code_locations={
                "location-1": with_auto_materialize_policy(
                    overlapping_freshness_inf[:-1], AutoMaterializePolicy.eager()
                ),
                "location-2": with_auto_materialize_policy(
                    overlapping_freshness_inf[-1:], AutoMaterializePolicy.eager()
                ),
            },
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation. But asset6 is in a different code location,
        # so it should not be included in the run request.
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[
            run_request(asset_keys=["asset2", "asset3", "asset4", "asset5"]),
            # run_request(asset_keys=["asset6"]),
        ],
    ),
    "multi_code_auto_materialize_policy_eager_with_freshness_policies_cross_code_location": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "location-1": with_auto_materialize_policy(
                overlapping_freshness_inf[:-1], AutoMaterializePolicy.eager()
            ),
            "location-2": with_auto_materialize_policy(
                overlapping_freshness_inf[-1:], AutoMaterializePolicy.eager()
            ),
        },
        cursor_from=AssetReconciliationScenario(
            assets=None,
            code_locations={
                "location-1": with_auto_materialize_policy(
                    overlapping_freshness_inf[:-1], AutoMaterializePolicy.eager()
                ),
                "location-2": with_auto_materialize_policy(
                    overlapping_freshness_inf[-1:], AutoMaterializePolicy.eager()
                ),
            },
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation. But asset6 is in a different code location,
        # so it should not be included in the run request.
        unevaluated_runs=[run(["asset2", "asset3", "asset4", "asset5"])],
        expected_run_requests=[
            run_request(asset_keys=["asset6"]),
        ],
    ),
    "multi_code_freshness_blank_slate": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "foo": with_auto_materialize_policy(
                diamond_freshness[:-1], AutoMaterializePolicy.lazy()
            ),
            "bar": with_auto_materialize_policy(
                diamond_freshness[-1:], AutoMaterializePolicy.lazy()
            ),
        },
        unevaluated_runs=[],
        # asset4 is in a separate location, can't be reconciled yet
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3"])],
    ),
    "multi_code_freshness_blank_slate_cross_code_location": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "foo": with_auto_materialize_policy(
                diamond_freshness[:-1],
                AutoMaterializePolicy(
                    for_freshness=True,
                    on_missing=False,
                    on_new_parent_data=False,
                    time_window_partition_scope_minutes=0,
                ),
            ),
            "bar": with_auto_materialize_policy(
                diamond_freshness[-1:],
                AutoMaterializePolicy(
                    for_freshness=True,
                    on_missing=False,
                    on_new_parent_data=False,
                    time_window_partition_scope_minutes=0,
                ),
            ),
        },
        unevaluated_runs=[run(["asset1", "asset2", "asset3"])],
        expected_run_requests=[run_request(asset_keys=["asset4"])],
    ),
    "multi_code_freshness_blank_slate_cross_code_location_2": AssetReconciliationScenario(
        assets=None,
        code_locations={
            "foo": with_auto_materialize_policy(
                diamond_freshness[:1],
                AutoMaterializePolicy(
                    for_freshness=True,
                    on_missing=False,
                    on_new_parent_data=False,
                    time_window_partition_scope_minutes=0,
                ),
            ),
            "bar": with_auto_materialize_policy(
                diamond_freshness[1:],
                AutoMaterializePolicy(
                    for_freshness=True,
                    on_missing=False,
                    on_new_parent_data=False,
                    time_window_partition_scope_minutes=0,
                ),
            ),
        },
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
}
