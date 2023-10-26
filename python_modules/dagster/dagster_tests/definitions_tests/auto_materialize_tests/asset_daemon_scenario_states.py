from dagster import AssetSpec
from .asset_daemon_scenario import AssetDaemonScenarioState

diamond = AssetDaemonScenarioState(
    asset_specs=[
        AssetSpec(key="A"),
        AssetSpec(key="B", deps=["A"]),
        AssetSpec(key="C", deps=["A"]),
        AssetSpec(key="D", deps=["B", "C"]),
    ]
)

one_asset = AssetDaemonScenarioState(asset_specs=[AssetSpec("A")])

two_assets_in_sequence = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"])],
)

three_assets_in_sequence = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["B"])],
)

two_assets_depend_on_one = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["A"])]
)

one_asset_depends_on_two = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C", deps=["A", "B"])]
)
