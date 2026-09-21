import dagster as dg
from dagster import DagsterInstance
from dagster._core.definitions.data_version import StaleCauseCategory, StaleStatus
from dagster._core.definitions.events import AssetKey
from dagster._utils.test.data_versions import (
    get_stale_status_resolver,
    materialize_asset,
    materialize_assets,
)


def _make_view_asset(name, deps, code_version=None):
    @dg.asset(name=name, deps=deps, is_virtual=True, code_version=code_version)
    def _view():
        pass

    return _view


def test_view_asset_staleness_lifecycle():
    @dg.asset
    def upstream():
        return 1

    view = _make_view_asset("view_asset", [upstream])

    @dg.asset(deps=[view])
    def downstream():
        return 1

    all_assets = [upstream, view, downstream]
    instance = DagsterInstance.ephemeral()

    # Before any materializations, view is MISSING like any other asset
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("view_asset")) == StaleStatus.MISSING

    # After materializing upstream, view is still FRESH
    materialize_asset(all_assets, upstream, instance)
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("view_asset")) == StaleStatus.FRESH

    # After materializing everything, view is still FRESH
    materialize_assets(all_assets, instance)
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("view_asset")) == StaleStatus.FRESH

    # Re-materialize upstream — view should remain FRESH
    materialize_asset(all_assets, upstream, instance)
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("view_asset")) == StaleStatus.FRESH


def test_staleness_traces_through_view():
    @dg.asset
    def source():
        return 1

    view = _make_view_asset("view_mid", [source])

    @dg.asset(deps=[view])
    def target():
        return 1

    all_assets = [source, view, target]
    instance = DagsterInstance.ephemeral()

    # Materialize source then target
    materialize_asset(all_assets, source, instance)
    materialize_asset(all_assets, target, instance)

    # Target should be fresh
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("target")) == StaleStatus.FRESH

    # Re-materialize source — target should become stale
    materialize_asset(all_assets, source, instance)
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("target")) == StaleStatus.STALE

    # Check the stale cause points to source
    causes = resolver.get_stale_causes(AssetKey("target"))
    data_causes = [c for c in causes if c.category == StaleCauseCategory.DATA]
    assert len(data_causes) > 0
    ancestor_keys = {c.dependency.asset_key for c in data_causes if c.dependency}
    assert AssetKey("source") in ancestor_keys


def test_staleness_traces_through_chain_of_views():
    @dg.asset
    def root():
        return 1

    view1 = _make_view_asset("view1", [root])
    view2 = _make_view_asset("view2", [view1])

    @dg.asset(deps=[view2])
    def leaf():
        return 1

    all_assets = [root, view1, view2, leaf]
    instance = DagsterInstance.ephemeral()

    # Materialize root then leaf
    materialize_asset(all_assets, root, instance)
    materialize_asset(all_assets, leaf, instance)

    # Leaf should be fresh
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.FRESH

    # Re-materialize root — leaf should become stale
    materialize_asset(all_assets, root, instance)
    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.STALE

    # Stale cause should reference root
    causes = resolver.get_stale_causes(AssetKey("leaf"))
    data_causes = [c for c in causes if c.category == StaleCauseCategory.DATA]
    assert len(data_causes) > 0
    ancestor_keys = {c.dependency.asset_key for c in data_causes if c.dependency}
    assert AssetKey("root") in ancestor_keys


def test_staleness_traces_through_complex_view_topology():
    """Tests staleness propagation through a complex branching view graph.

    Topology:
        root_a ──► view_a1 ──► view_a2 ──┐
                                          ├──► view_join ──► view_tail ──► leaf
        root_b ──► view_b1 ──────────────┘
                       │
                       └──► view_b2 ──► leaf_b

    - Diamond: root_a flows through a chain (view_a1 → view_a2) that merges
      with root_b's path (view_b1) at view_join, then continues through
      view_tail to leaf.
    - Fork: view_b1 also feeds view_b2 → leaf_b (a separate branch).
    """

    @dg.asset
    def root_a():
        return 1

    @dg.asset
    def root_b():
        return 1

    view_a1 = _make_view_asset("view_a1", [root_a])
    view_a2 = _make_view_asset("view_a2", [view_a1])
    view_b1 = _make_view_asset("view_b1", [root_b])
    view_join = _make_view_asset("view_join", [view_a2, view_b1])
    view_tail = _make_view_asset("view_tail", [view_join])
    view_b2 = _make_view_asset("view_b2", [view_b1])

    @dg.asset(deps=[view_tail])
    def leaf():
        return 1

    @dg.asset(deps=[view_b2])
    def leaf_b():
        return 1

    all_assets = [
        root_a,
        root_b,
        view_a1,
        view_a2,
        view_b1,
        view_join,
        view_tail,
        view_b2,
        leaf,
        leaf_b,
    ]
    instance = DagsterInstance.ephemeral()

    # --- Baseline: materialize roots, then leaves ---
    materialize_asset(all_assets, root_a, instance)
    materialize_asset(all_assets, root_b, instance)
    materialize_asset(all_assets, leaf, instance)
    materialize_asset(all_assets, leaf_b, instance)

    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.FRESH
    assert resolver.get_status(AssetKey("leaf_b")) == StaleStatus.FRESH

    # --- Re-materialize root_a only ---
    # leaf should become stale (root_a → view_a1 → view_a2 → view_join → view_tail → leaf)
    # leaf_b should stay fresh (root_a is not an ancestor of leaf_b)
    materialize_asset(all_assets, root_a, instance)

    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.STALE
    assert resolver.get_status(AssetKey("leaf_b")) == StaleStatus.FRESH

    # Stale cause for leaf should reference root_a
    causes = resolver.get_stale_causes(AssetKey("leaf"))
    data_causes = [c for c in causes if c.category == StaleCauseCategory.DATA]
    cause_dep_keys = {c.dependency.asset_key for c in data_causes if c.dependency}
    assert AssetKey("root_a") in cause_dep_keys
    assert AssetKey("root_b") not in cause_dep_keys

    # --- Re-materialize leaf to reset, then re-materialize root_b ---
    materialize_asset(all_assets, leaf, instance)
    materialize_asset(all_assets, leaf_b, instance)
    materialize_asset(all_assets, root_b, instance)

    resolver = get_stale_status_resolver(instance, all_assets)

    # leaf should be stale (root_b → view_b1 → view_join → view_tail → leaf)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.STALE
    # leaf_b should also be stale (root_b → view_b1 → view_b2 → leaf_b)
    assert resolver.get_status(AssetKey("leaf_b")) == StaleStatus.STALE

    # Both should cite root_b as the stale cause
    for leaf_key in ["leaf", "leaf_b"]:
        causes = resolver.get_stale_causes(AssetKey(leaf_key))
        data_causes = [c for c in causes if c.category == StaleCauseCategory.DATA]
        cause_dep_keys = {c.dependency.asset_key for c in data_causes if c.dependency}
        assert AssetKey("root_b") in cause_dep_keys

    # --- Re-materialize both roots: both leaves should become stale with both causes ---
    materialize_asset(all_assets, leaf, instance)
    materialize_asset(all_assets, leaf_b, instance)
    materialize_asset(all_assets, root_a, instance)
    materialize_asset(all_assets, root_b, instance)

    resolver = get_stale_status_resolver(instance, all_assets)
    assert resolver.get_status(AssetKey("leaf")) == StaleStatus.STALE

    causes = resolver.get_stale_causes(AssetKey("leaf"))
    data_causes = [c for c in causes if c.category == StaleCauseCategory.DATA]
    cause_dep_keys = {c.dependency.asset_key for c in data_causes if c.dependency}
    # leaf should see both roots as stale causes through the diamond
    assert AssetKey("root_a") in cause_dep_keys
    assert AssetKey("root_b") in cause_dep_keys


def test_view_code_version_stale():
    @dg.asset
    def upstream():
        return 1

    view_v1 = _make_view_asset("my_view", [upstream], code_version="v1")

    all_assets_v1 = [upstream, view_v1]
    instance = DagsterInstance.ephemeral()

    # Materialize upstream then the view
    materialize_asset(all_assets_v1, upstream, instance)
    materialize_asset(all_assets_v1, view_v1, instance)

    # View should be fresh with code_version="v1"
    resolver = get_stale_status_resolver(instance, all_assets_v1)
    assert resolver.get_status(AssetKey("my_view")) == StaleStatus.FRESH

    # Now redefine the view with a new code version
    view_v2 = _make_view_asset("my_view", [upstream], code_version="v2")

    all_assets_v2 = [upstream, view_v2]

    # View should now be stale due to code version change
    resolver = get_stale_status_resolver(instance, all_assets_v2)
    assert resolver.get_status(AssetKey("my_view")) == StaleStatus.STALE

    causes = resolver.get_stale_causes(AssetKey("my_view"))
    code_causes = [c for c in causes if c.category == StaleCauseCategory.CODE]
    assert len(code_causes) == 1
    assert "new code version" in code_causes[0].reason
