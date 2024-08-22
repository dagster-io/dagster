from typing import Sequence

from dagster import AssetsDefinition, FreshnessPolicy
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

from ...scenario_utils.base_scenario import AssetReconciliationScenario, asset_def, run, run_request
from .basic_scenarios import diamond

freshness_30m = FreshnessPolicy(maximum_lag_minutes=30)
freshness_inf = FreshnessPolicy(maximum_lag_minutes=99999)

diamond_freshness = diamond[:-1] + [
    asset_def("asset4", ["asset2", "asset3"], freshness_policy=freshness_30m)
]

overlapping_freshness_inf = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=freshness_inf),
]


def with_auto_materialize_policy(
    assets_defs: Sequence[AssetsDefinition], auto_materialize_policy: AutoMaterializePolicy
) -> Sequence[AssetsDefinition]:
    ret = []
    for assets_def in assets_defs:
        ret.append(
            AssetsDefinition.dagster_internal_init(
                **{
                    **assets_def.get_attributes_dict(),
                    **{
                        "specs": [
                            spec._replace(
                                automation_condition=auto_materialize_policy.to_automation_condition()
                            )
                            for spec in assets_def.specs
                        ]
                    },
                }
            )
        )
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
                AutoMaterializePolicy.lazy(max_materializations_per_minute=None),
            ),
            "bar": with_auto_materialize_policy(
                diamond_freshness[-1:],
                AutoMaterializePolicy.lazy(max_materializations_per_minute=None),
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
                AutoMaterializePolicy.lazy(max_materializations_per_minute=None),
            ),
            "bar": with_auto_materialize_policy(
                diamond_freshness[1:],
                AutoMaterializePolicy.lazy(max_materializations_per_minute=None),
            ),
        },
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
}
