"""Tests for dbt mesh support via the ``external_packages`` component field.

When ``external_packages: ["silver_project"]`` is set on ``DbtProjectComponent`` or
``DbtCloudComponent``:

1. Models with ``package_name in external_packages`` are auto-excluded from the
   materializable graph (so ``dbt build`` doesn't try to rebuild them).
2. Those models are emitted as observable external stub ``AssetSpec`` objects so
   downstream lineage is preserved. When another Dagster code location declares the
   upstream project's real specs at the same ``AssetKey``, the stub yields precedence
   and the graph stitches across code locations.
"""

from typing import Any

from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
)
from dagster_dbt.asset_specs import (
    DAGSTER_DBT_EXTERNAL_PACKAGE_METADATA_KEY,
    build_dbt_external_package_asset_specs,
)


def _model_node(
    name: str,
    package: str = "gold_project",
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "resource_type": "model",
        "unique_id": f"model.{package}.{name}",
        "name": name,
        "package_name": package,
        "config": {"materialized": "table"},
        "depends_on": {"nodes": depends_on or []},
        "fqn": [package, name],
    }


def _synthetic_manifest(nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "metadata": {"adapter_type": "duckdb"},
        "nodes": nodes,
        "sources": {},
        "exposures": {},
        "metrics": {},
        "semantic_models": {},
        "groups": {},
        "child_map": {},
        "parent_map": {},
    }


def test_empty_external_packages_returns_empty() -> None:
    manifest = _synthetic_manifest({"model.gold.a": _model_node("a")})
    assert build_dbt_external_package_asset_specs(manifest=manifest, external_packages=[]) == []


def test_external_package_model_emitted_as_stub() -> None:
    manifest = _synthetic_manifest(
        {
            "model.gold_project.gold_mart": _model_node("gold_mart", package="gold_project"),
            "model.silver_project.silver_stage": _model_node(
                "silver_stage", package="silver_project"
            ),
        }
    )
    specs = build_dbt_external_package_asset_specs(
        manifest=manifest, external_packages=["silver_project"]
    )
    assert len(specs) == 1
    spec = specs[0]
    assert spec.key == AssetKey("silver_stage")
    assert spec.metadata.get(SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET) is True
    assert spec.metadata[DAGSTER_DBT_EXTERNAL_PACKAGE_METADATA_KEY] == "silver_project"


def test_own_package_models_not_emitted() -> None:
    # Only models from external packages should be emitted — the current project's own
    # models are handled by the standard `@dbt_assets` path.
    manifest = _synthetic_manifest(
        {
            "model.gold_project.gold_mart": _model_node("gold_mart", package="gold_project"),
        }
    )
    specs = build_dbt_external_package_asset_specs(
        manifest=manifest, external_packages=["silver_project"]
    )
    assert specs == []


def test_multiple_external_packages_all_emitted() -> None:
    manifest = _synthetic_manifest(
        {
            "model.silver_project.s1": _model_node("s1", package="silver_project"),
            "model.silver_project.s2": _model_node("s2", package="silver_project"),
            "model.shared_ref.r1": _model_node("r1", package="shared_ref"),
            "model.gold_project.g1": _model_node("g1", package="gold_project"),
        }
    )
    specs = build_dbt_external_package_asset_specs(
        manifest=manifest, external_packages=["silver_project", "shared_ref"]
    )
    keys = {spec.key for spec in specs}
    assert keys == {AssetKey("s1"), AssetKey("s2"), AssetKey("r1")}
    packages = {
        spec.key.to_user_string(): spec.metadata[DAGSTER_DBT_EXTERNAL_PACKAGE_METADATA_KEY]
        for spec in specs
    }
    assert packages == {
        "s1": "silver_project",
        "s2": "silver_project",
        "r1": "shared_ref",
    }


def test_non_model_resources_from_external_package_ignored() -> None:
    # We only emit stubs for models — sources/seeds/snapshots/tests from external packages
    # are handled by their own resource-type paths (sources have their own spec builder,
    # tests can flow through the shared asset-check machinery, etc.).
    manifest = _synthetic_manifest(
        {
            "model.silver_project.s1": _model_node("s1", package="silver_project"),
            "seed.silver_project.raw_seed": {
                "resource_type": "seed",
                "unique_id": "seed.silver_project.raw_seed",
                "name": "raw_seed",
                "package_name": "silver_project",
                "config": {},
                "depends_on": {"nodes": []},
                "fqn": ["silver_project", "seeds", "raw_seed"],
            },
        }
    )
    specs = build_dbt_external_package_asset_specs(
        manifest=manifest, external_packages=["silver_project"]
    )
    assert {spec.key for spec in specs} == {AssetKey("s1")}


def test_deduplicated_by_asset_key_first_wins() -> None:
    # Two models with the same AssetKey (via meta.dagster.asset_key override) from the
    # same external package should dedupe first-wins.
    props_a = _model_node("a", package="silver_project")
    props_a["meta"] = {"dagster": {"asset_key": ["shared_customers"]}}
    props_b = _model_node("b", package="silver_project")
    props_b["meta"] = {"dagster": {"asset_key": ["shared_customers"]}}
    manifest = _synthetic_manifest(
        {"model.silver_project.a": props_a, "model.silver_project.b": props_b}
    )
    specs = build_dbt_external_package_asset_specs(
        manifest=manifest, external_packages=["silver_project"]
    )
    assert len(specs) == 1
