"""Tests for state-aware `dbt/state` tagging.

Setting `state_manifest_path` on `DbtProjectComponent` / `DbtCloudComponent` compares
per-model `checksum.checksum` between a current and prod-state manifest. Each dbt model
spec is tagged with `dbt/state=modified|unchanged|new`, letting users select changed
models via `tag:dbt/state=modified` in launch commands or automation conditions.

Only SQL-body changes are detected (mirrors dbt's `state:modified.sql` sub-selector).
Full `state:modified` semantics (config, macros, contract, etc.) require running
`dbt ls --state <path> --select state:modified` at CI time.
"""

from typing import Any

from dagster_dbt.asset_utils import (
    DBT_STATE_MODIFIED,
    DBT_STATE_NEW,
    DBT_STATE_UNCHANGED,
    compute_dbt_state_tags,
)


def _model_node(name: str, checksum: str = "abc", package: str = "my_project") -> dict[str, Any]:
    return {
        "resource_type": "model",
        "unique_id": f"model.{package}.{name}",
        "name": name,
        "checksum": {"name": "sha256", "checksum": checksum},
    }


def _seed_node(name: str, checksum: str = "abc") -> dict[str, Any]:
    return {
        "resource_type": "seed",
        "unique_id": f"seed.my_project.{name}",
        "name": name,
        "checksum": {"name": "sha256", "checksum": checksum},
    }


def _manifest(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    return {"nodes": {node["unique_id"]: node for node in nodes}}


def test_modified_model_detected() -> None:
    current = _manifest([_model_node("customers", checksum="new-hash")])
    state = _manifest([_model_node("customers", checksum="old-hash")])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {"model.my_project.customers": DBT_STATE_MODIFIED}


def test_unchanged_model_detected() -> None:
    current = _manifest([_model_node("customers", checksum="same-hash")])
    state = _manifest([_model_node("customers", checksum="same-hash")])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {"model.my_project.customers": DBT_STATE_UNCHANGED}


def test_new_model_detected() -> None:
    # Model exists in current but not in state -> new.
    current = _manifest([_model_node("customers"), _model_node("orders", checksum="fresh")])
    state = _manifest([_model_node("customers")])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {
        "model.my_project.customers": DBT_STATE_UNCHANGED,
        "model.my_project.orders": DBT_STATE_NEW,
    }


def test_seeds_and_snapshots_excluded() -> None:
    # Only `model` resources are compared. Seeds/snapshots aren't tagged.
    current = _manifest([_model_node("customers"), _seed_node("raw_customers")])
    state = _manifest([_model_node("customers")])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert "seed.my_project.raw_customers" not in tags


def test_missing_checksum_treated_as_different() -> None:
    # If current has a checksum and state's is missing (or vice versa), they don't match ->
    # marked as modified. This ensures we err on the safe side rather than silently ignoring.
    current = _manifest([_model_node("customers", checksum="abc")])
    state_node = _model_node("customers", checksum="abc")
    del state_node["checksum"]
    state = _manifest([state_node])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {"model.my_project.customers": DBT_STATE_MODIFIED}


def test_empty_state_manifest_marks_everything_new() -> None:
    current = _manifest([_model_node("customers"), _model_node("orders")])
    state = _manifest([])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {
        "model.my_project.customers": DBT_STATE_NEW,
        "model.my_project.orders": DBT_STATE_NEW,
    }


def test_empty_current_manifest_returns_empty() -> None:
    current = _manifest([])
    state = _manifest([_model_node("customers")])
    assert compute_dbt_state_tags(current_manifest=current, state_manifest=state) == {}


def test_state_manifest_with_extra_models_ignored() -> None:
    # Models that exist in state but not in current shouldn't cause errors — they're
    # simply not part of the returned tag map (only current models get tagged).
    current = _manifest([_model_node("customers")])
    state = _manifest([_model_node("customers"), _model_node("removed_model")])
    tags = compute_dbt_state_tags(current_manifest=current, state_manifest=state)
    assert tags == {"model.my_project.customers": DBT_STATE_UNCHANGED}
    assert "model.my_project.removed_model" not in tags
