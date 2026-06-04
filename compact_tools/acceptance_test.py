"""Acceptance test for the lightweight Dagster effort.

Three assets with dependencies that must materialize successfully after every
size-reduction change. Run with the project venv:

    .venv/bin/python compact_tools/acceptance_test.py

Exits non-zero if materialization fails or produces unexpected values.
"""

from dagster import asset, materialize


@asset
def upstream() -> int:
    return 1


@asset
def midstream(upstream: int) -> int:
    return upstream + 10


@asset
def downstream(midstream: int) -> int:
    return midstream * 2


def main() -> None:
    result = materialize([upstream, midstream, downstream])
    assert result.success, "materialize() did not succeed"

    expected = {"upstream": 1, "midstream": 11, "downstream": 22}
    for name, want in expected.items():
        got = result.output_for_node(name)
        assert got == want, f"{name}: expected {want}, got {got}"

    print("ACCEPTANCE TEST PASSED: 3 assets materialized with correct values")


if __name__ == "__main__":
    main()
