"""Tests for surfacing dbt semantic_models and metrics as observable external Dagster
``AssetSpec`` objects.

Emitted specs give users a downstream lineage view of dbt's semantic layer: semantic_models
depend on the model they're built from; metrics depend on the semantic_models they
aggregate. Opt-in via ``translation_settings.enable_semantic_layer_assets``.
"""

from typing import Any

from dagster import AssetKey
from dagster_dbt.asset_specs import (
    DAGSTER_DBT_METRIC_LABEL_METADATA_KEY,
    DAGSTER_DBT_METRIC_TYPE_METADATA_KEY,
    DAGSTER_DBT_SEMANTIC_MODEL_DIMENSIONS_METADATA_KEY,
    DAGSTER_DBT_SEMANTIC_MODEL_ENTITIES_METADATA_KEY,
    DAGSTER_DBT_SEMANTIC_MODEL_MEASURES_METADATA_KEY,
    build_dbt_semantic_layer_asset_specs,
)


def _model_node(name: str) -> dict[str, Any]:
    return {
        "resource_type": "model",
        "name": name,
        "unique_id": f"model.my_project.{name}",
        "config": {"materialized": "table"},
        "depends_on": {"nodes": []},
    }


def _semantic_model(
    name: str,
    *,
    upstream_model: str,
    measures: list[str] | None = None,
    dimensions: list[str] | None = None,
    entities: list[str] | None = None,
    description: str = "",
) -> dict[str, Any]:
    return {
        "resource_type": "semantic_model",
        "unique_id": f"semantic_model.my_project.{name}",
        "name": name,
        "config": {},
        "description": description,
        "depends_on": {"nodes": [f"model.my_project.{upstream_model}"]},
        "meta": {},
        "measures": [{"name": m} for m in (measures or [])],
        "dimensions": [{"name": d} for d in (dimensions or [])],
        "entities": [{"name": e} for e in (entities or [])],
    }


def _metric(
    name: str,
    metric_type: str = "simple",
    *,
    upstream_semantic_models: list[str] | None = None,
    label: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    return {
        "resource_type": "metric",
        "unique_id": f"metric.my_project.{name}",
        "name": name,
        "type": metric_type,
        "label": label,
        "description": description,
        "config": {},
        "meta": {},
        "depends_on": {
            "nodes": [f"semantic_model.my_project.{sm}" for sm in (upstream_semantic_models or [])]
        },
    }


def _synthetic_manifest(
    nodes: dict[str, dict[str, Any]] | None = None,
    semantic_models: dict[str, dict[str, Any]] | None = None,
    metrics: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "metadata": {"adapter_type": "duckdb"},
        "nodes": nodes or {},
        "sources": {},
        "exposures": {},
        "metrics": metrics or {},
        "semantic_models": semantic_models or {},
        "saved_queries": {},
        "groups": {},
        "child_map": {},
        "parent_map": {},
    }


def test_empty_manifest_returns_empty() -> None:
    specs = build_dbt_semantic_layer_asset_specs(manifest=_synthetic_manifest())
    assert specs == []


def test_semantic_model_emitted_with_upstream_model_dep() -> None:
    manifest = _synthetic_manifest(
        nodes={"model.my_project.orders": _model_node("orders")},
        semantic_models={
            "semantic_model.my_project.orders_sm": _semantic_model(
                "orders_sm",
                upstream_model="orders",
                measures=["revenue", "order_count"],
                dimensions=["order_date"],
                entities=["customer"],
            )
        },
    )
    specs = build_dbt_semantic_layer_asset_specs(manifest=manifest)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.key == AssetKey("orders_sm")
    assert spec.kinds == {"semantic_model"}
    dep_keys = {dep.asset_key for dep in spec.deps}
    assert dep_keys == {AssetKey("orders")}
    assert spec.metadata[DAGSTER_DBT_SEMANTIC_MODEL_MEASURES_METADATA_KEY] == [
        "revenue",
        "order_count",
    ]
    assert spec.metadata[DAGSTER_DBT_SEMANTIC_MODEL_DIMENSIONS_METADATA_KEY] == ["order_date"]
    assert spec.metadata[DAGSTER_DBT_SEMANTIC_MODEL_ENTITIES_METADATA_KEY] == ["customer"]


def test_metric_emitted_with_semantic_model_dep() -> None:
    manifest = _synthetic_manifest(
        nodes={"model.my_project.orders": _model_node("orders")},
        semantic_models={
            "semantic_model.my_project.orders_sm": _semantic_model(
                "orders_sm", upstream_model="orders"
            )
        },
        metrics={
            "metric.my_project.total_revenue": _metric(
                "total_revenue",
                metric_type="simple",
                upstream_semantic_models=["orders_sm"],
                label="Total Revenue",
            )
        },
    )
    specs = build_dbt_semantic_layer_asset_specs(manifest=manifest)
    metric_spec = next(spec for spec in specs if spec.key == AssetKey("total_revenue"))
    assert metric_spec.kinds == {"metric"}
    dep_keys = {dep.asset_key for dep in metric_spec.deps}
    assert dep_keys == {AssetKey("orders_sm")}
    assert metric_spec.metadata[DAGSTER_DBT_METRIC_TYPE_METADATA_KEY] == "simple"
    assert metric_spec.metadata[DAGSTER_DBT_METRIC_LABEL_METADATA_KEY] == "Total Revenue"


def test_metric_label_omitted_when_missing() -> None:
    manifest = _synthetic_manifest(
        metrics={
            "metric.my_project.total_revenue": _metric(
                "total_revenue", label=None, upstream_semantic_models=[]
            )
        }
    )
    spec = build_dbt_semantic_layer_asset_specs(manifest=manifest)[0]
    assert DAGSTER_DBT_METRIC_LABEL_METADATA_KEY not in spec.metadata


def test_metric_types_normalized_to_lowercase() -> None:
    manifest = _synthetic_manifest(
        metrics={
            f"metric.my_project.{metric_type}_metric": _metric(
                f"{metric_type}_metric", metric_type=metric_type
            )
            for metric_type in ("Simple", "RATIO", "cumulative", "Derived")
        }
    )
    specs = build_dbt_semantic_layer_asset_specs(manifest=manifest)
    types = {
        spec.key.to_user_string(): spec.metadata[DAGSTER_DBT_METRIC_TYPE_METADATA_KEY]
        for spec in specs
    }
    assert types["Simple_metric"] == "simple"
    assert types["RATIO_metric"] == "ratio"
    assert types["cumulative_metric"] == "cumulative"
    assert types["Derived_metric"] == "derived"


def test_multiple_semantic_models_and_metrics() -> None:
    manifest = _synthetic_manifest(
        nodes={
            "model.my_project.orders": _model_node("orders"),
            "model.my_project.customers": _model_node("customers"),
        },
        semantic_models={
            "semantic_model.my_project.orders_sm": _semantic_model(
                "orders_sm", upstream_model="orders"
            ),
            "semantic_model.my_project.customers_sm": _semantic_model(
                "customers_sm", upstream_model="customers"
            ),
        },
        metrics={
            "metric.my_project.m1": _metric("m1", upstream_semantic_models=["orders_sm"]),
            "metric.my_project.m2": _metric(
                "m2", upstream_semantic_models=["orders_sm", "customers_sm"]
            ),
        },
    )
    specs = build_dbt_semantic_layer_asset_specs(manifest=manifest)
    assert len(specs) == 4
    kinds_by_key = {spec.key: spec.kinds for spec in specs}
    assert kinds_by_key[AssetKey("orders_sm")] == {"semantic_model"}
    assert kinds_by_key[AssetKey("customers_sm")] == {"semantic_model"}
    assert kinds_by_key[AssetKey("m1")] == {"metric"}
    assert kinds_by_key[AssetKey("m2")] == {"metric"}


def test_missing_upstream_skips_that_dep_silently() -> None:
    # Dep on a semantic_model that isn't in the manifest should be silently skipped,
    # matching the exposure spec behavior (stale references shouldn't fail load).
    manifest = _synthetic_manifest(
        nodes={"model.my_project.orders": _model_node("orders")},
        semantic_models={
            "semantic_model.my_project.orders_sm": _semantic_model(
                "orders_sm", upstream_model="orders"
            ),
        },
        metrics={
            "metric.my_project.m1": _metric(
                "m1", upstream_semantic_models=["orders_sm", "does_not_exist"]
            )
        },
    )
    metric_spec = next(
        spec
        for spec in build_dbt_semantic_layer_asset_specs(manifest=manifest)
        if spec.key == AssetKey("m1")
    )
    dep_keys = {dep.asset_key for dep in metric_spec.deps}
    assert dep_keys == {AssetKey("orders_sm")}
