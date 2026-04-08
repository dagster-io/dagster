"""Tests for transitive step dependencies through view assets.

When A(non-view) -> B(view) -> C(non-view) and B is excluded from the run selection,
C should still wait for A via ordering dependencies on the FromLoadableAsset input source.
"""

import dagster as dg
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.execution.api import create_execution_plan
from dagster._core.snap.execution_plan_snapshot import snapshot_from_execution_plan


def _resolve_job(assets, job):
    return job.resolve(asset_graph=AssetGraph.from_assets(assets))


def test_basic_view_transitive_dep():
    """A -> B(view) -> C, select A+C: C depends on A."""

    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=["a"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["b"])
    def c() -> None: ...

    all_assets = [a, b, c]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.assets("a", "c")),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    assert "a" in deps
    assert "c" in deps
    # C should depend on A (transitive through excluded view B)
    assert "a" in deps["c"]

    # Verify snapshot also captures the ordering dependency
    snap = snapshot_from_execution_plan(plan, "test")
    assert "a" in snap.step_deps["c"]


def test_chain_of_views():
    """A -> B(view) -> C(view) -> D, select A+D: D depends on A."""

    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=["a"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["b"], is_virtual=True)
    def c() -> None: ...

    @dg.asset(deps=["c"])
    def d() -> None: ...

    all_assets = [a, b, c, d]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.assets("a", "d")),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    assert "d" in deps
    assert "a" in deps["d"]


def test_diamond_through_view():
    """A -> B(view) -> D, A -> C -> D, select A+C+D: D depends on A (via view) and C (direct)."""

    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=["a"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["a"])
    def c() -> None: ...

    @dg.asset(deps=["b", "c"])
    def d() -> None: ...

    all_assets = [a, b, c, d]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.assets("a", "c", "d")),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    assert "d" in deps
    # D depends on A (transitive through view B) and C (direct)
    assert "a" in deps["d"]
    assert "c" in deps["d"]


def test_multiple_non_view_ancestors():
    """A -> B(view), C -> B(view), B -> D, select A+C+D: D depends on A and C."""

    @dg.asset
    def a() -> None: ...

    @dg.asset
    def c() -> None: ...

    @dg.asset(deps=["a", "c"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["b"])
    def d() -> None: ...

    all_assets = [a, c, b, d]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.assets("a", "c", "d")),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    assert "d" in deps
    assert "a" in deps["d"]
    assert "c" in deps["d"]


def test_view_selected_no_ordering_deps():
    """A -> B(view) -> C, all selected: normal deps, no ordering deps needed."""

    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=["a"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["b"])
    def c() -> None: ...

    all_assets = [a, b, c]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.all()),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    # When view is selected, normal FromStepOutput deps apply
    assert "b" in deps
    assert "a" in deps["b"]
    assert "c" in deps
    assert "b" in deps["c"]


def test_ancestor_not_in_plan():
    """A -> B(view) -> C, select only C: no crash, A is filtered by executable_map."""

    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=["a"], is_virtual=True)
    def b() -> None: ...

    @dg.asset(deps=["b"])
    def c() -> None: ...

    all_assets = [a, b, c]
    job = _resolve_job(
        all_assets,
        dg.define_asset_job("test_job", selection=dg.AssetSelection.assets("c")),
    )

    plan = create_execution_plan(job)
    deps = plan.get_executable_step_deps()

    # C should still be in the plan with no deps (A is not in selection)
    assert "c" in deps
    assert deps["c"] == set()
