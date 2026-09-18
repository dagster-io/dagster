"""
Regression tests for dagster issue #34184:
compute_logical_data_version must use an injective encoding when joining hash
components, so that two genuinely different upstream states never produce the
same data version.

These tests call the production function directly.
"""
import dagster as dg
from dagster._core.definitions.data_version import (
    DataVersion,
    compute_logical_data_version,
)


def test_boundary_collision_is_prevented():
    """
    Without an injective encoding, ("ab", "c") and ("a", "bc") produce the
    same joined string and therefore the same hash.  With length-prefix
    encoding they produce different hashes.

    This test FAILS on the unpatched code and PASSES with the fix.
    """
    key = dg.AssetKey(["upstream"])

    v1 = compute_logical_data_version("ab", {key: DataVersion("c")})
    v2 = compute_logical_data_version("a",  {key: DataVersion("bc")})

    assert v1 != v2, (
        "compute_logical_data_version must produce different hashes for "
        "('ab', 'c') and ('a', 'bc') — use an injective encoding"
    )


def test_nul_boundary_collision_is_prevented():
    """
    A NUL-byte delimiter is not injective when component values can contain
    NUL characters.  Length-prefix encoding is injective for all strings.
    """
    key = dg.AssetKey(["upstream"])

    v1 = compute_logical_data_version("a\x00b", {key: DataVersion("c")})
    v2 = compute_logical_data_version("a",       {key: DataVersion("b\x00c")})

    assert v1 != v2, (
        "compute_logical_data_version must produce different hashes even "
        "when component values contain NUL characters"
    )


def test_multi_upstream_boundary_collision_is_prevented():
    """
    Three-component case: code_version + two upstream versions.
    Without an injective encoding, "v1" + "xy" + "z" == "v1" + "x" + "yz".
    """
    key_a = dg.AssetKey(["alpha"])
    key_b = dg.AssetKey(["beta"])

    v1 = compute_logical_data_version(
        "v1", {key_a: DataVersion("xy"), key_b: DataVersion("z")}
    )
    v2 = compute_logical_data_version(
        "v1", {key_a: DataVersion("x"), key_b: DataVersion("yz")}
    )

    assert v1 != v2


def test_same_inputs_produce_same_hash():
    """Sanity check: identical inputs must still produce the same hash."""
    key = dg.AssetKey(["upstream"])

    v1 = compute_logical_data_version("code1", {key: DataVersion("data1")})
    v2 = compute_logical_data_version("code1", {key: DataVersion("data1")})

    assert v1 == v2
