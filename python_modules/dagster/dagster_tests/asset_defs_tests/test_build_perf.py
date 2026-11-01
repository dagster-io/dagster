import gc
import statistics
import time

import dagster as dg


class _Resource(dg.ConfigurableResource):
    pass


def _build_asset(i: int) -> dg.AssetsDefinition:
    @dg.asset(
        key_prefix=["prefix", "group"],
        name=f"asset_{i}",
        group_name="group",
        owners=["team:perf"],
        tags={"a": "1", "b": "2"},
        metadata={"m": "v"},
    )
    def _a(context: dg.AssetExecutionContext, resource: _Resource) -> int:
        return 1

    return _a


def _build_check(i: int, asset_def: dg.AssetsDefinition) -> dg.AssetChecksDefinition:
    @dg.asset_check(asset=asset_def, name=f"check_{i}", metadata={"m": "v"})
    def _c(resource: _Resource) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    return _c


def test_construction_scales() -> None:
    """Smoke-test the retained-results workload without a hardware-dependent time limit."""
    n = 1000
    assets = [_build_asset(i) for i in range(n)]
    checks = [_build_check(i, asset_def) for i, asset_def in enumerate(assets)]
    assert len(assets) == len(checks) == n


def benchmark_construction(n: int = 1000, repeats: int = 7) -> list[float]:
    """Time fresh definitions with imports warmed and all results retained.

    Run with: python -m dagster_tests.asset_defs_tests.test_build_perf
    GC remains enabled; explicit collection and cleanup are outside the timed region.
    """
    _build_check(n, _build_asset(n))
    timings = []
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter()
        assets = [_build_asset(i) for i in range(n)]
        checks = [_build_check(i, asset_def) for i, asset_def in enumerate(assets)]
        timings.append((time.perf_counter() - start) * 1000)
        del assets, checks
    return timings


if __name__ == "__main__":
    timings = benchmark_construction()
    print(  # noqa: T201
        f"1000 assets + 1000 checks: median {statistics.median(timings):.1f} ms; "
        f"runs {[round(value, 1) for value in timings]}"
    )
