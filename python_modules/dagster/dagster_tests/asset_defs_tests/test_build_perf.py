import time

import dagster as dg
import pytest


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


def test_construction_scales(capsys: pytest.CaptureFixture) -> None:
    """Build many asset/check definitions, and check it is not too slow.

    Run with ``-s`` to see the per-definition timing.
    """
    n = 1000

    _build_check(n, _build_asset(n)) # Warm up import/first-call costs

    start = time.perf_counter()
    assets = [_build_asset(i) for i in range(n)]
    for i, asset_def in enumerate(assets):
        _build_check(i, asset_def)
    elapsed = time.perf_counter() - start

    per_def_us = elapsed / (2 * n) * 1e6
    with capsys.disabled():
        print(  # noqa: T201, used for benchmarking
            f"\nbuilt {n} assets + {n} checks in {elapsed * 1e3:.0f} ms ({per_def_us:.1f} us/def)"
        )

    # Very rough upper bound: construction should be ~0.1-0.3 ms/def,
    # 5 ms/def should indicate a real regression.
    assert elapsed < 2 * n * 5e-3, f"definition construction is too slow: {per_def_us:.1f} us/def"
