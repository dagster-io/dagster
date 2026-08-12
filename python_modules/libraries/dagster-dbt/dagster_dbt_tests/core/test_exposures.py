"""Tests for surfacing dbt exposures as observable external Dagster ``AssetSpec`` objects.

Exposures are declared in dbt ``exposures.yml`` and represent downstream consumers of dbt
models (BI dashboards, notebooks, ML models, applications, analyses). Emitting them as
downstream ``AssetSpec`` objects gives users a downstream relationship in the Dagster
graph — "if this model breaks, which dashboards are affected?" — without materializing
anything. Opt-in via ``translation_settings.enable_exposure_assets``.
"""

from typing import Any

from dagster import AssetKey
from dagster_dbt.asset_specs import (
    DAGSTER_DBT_EXPOSURE_MATURITY_METADATA_KEY,
    DAGSTER_DBT_EXPOSURE_TYPE_METADATA_KEY,
    DAGSTER_DBT_EXPOSURE_URL_METADATA_KEY,
    build_dbt_exposure_asset_specs,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


def _model_props(name: str) -> dict[str, Any]:
    return {
        "resource_type": "model",
        "name": name,
        "unique_id": f"model.my_project.{name}",
        "config": {"materialized": "table"},
        "depends_on": {"nodes": []},
    }


def _exposure_props(
    name: str,
    exposure_type: str = "dashboard",
    *,
    upstream_models: list[str] | None = None,
    url: str | None = "https://dashboards.example.com/x",
    maturity: str | None = "high",
    description: str = "an important dashboard",
    tags: list[str] | None = None,
    owner_email: str | None = "team@example.com",
) -> dict[str, Any]:
    return {
        "resource_type": "exposure",
        "unique_id": f"exposure.my_project.{name}",
        "name": name,
        "type": exposure_type,
        "description": description,
        "url": url,
        "maturity": maturity,
        "owner": ({"email": owner_email} if owner_email else {}),
        "tags": tags or [],
        "meta": {},
        # Exposures always carry a `config` field in the manifest; include it here
        # so the shared `default_asset_key_fn` doesn't KeyError on synthetic fixtures.
        "config": {},
        "depends_on": {"nodes": [f"model.my_project.{model}" for model in (upstream_models or [])]},
    }


def _synthetic_manifest(
    exposures: dict[str, dict[str, Any]] | None = None,
    nodes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "metadata": {"adapter_type": "duckdb"},
        "nodes": nodes or {},
        "sources": {},
        "exposures": exposures or {},
        "metrics": {},
        "semantic_models": {},
        "saved_queries": {},
        "groups": {},
        "child_map": {},
        "parent_map": {},
    }


def test_no_exposures_returns_empty() -> None:
    specs = build_dbt_exposure_asset_specs(manifest=_synthetic_manifest())
    assert specs == []


def test_exposure_emitted_with_kind_from_type() -> None:
    manifest = _synthetic_manifest(
        exposures={"exposure.my_project.dash": _exposure_props("dash", "dashboard")}
    )
    specs = build_dbt_exposure_asset_specs(manifest=manifest)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.key == AssetKey("dash")
    assert spec.kinds == {"dashboard"}


def test_exposure_types_map_to_distinct_kinds() -> None:
    manifest = _synthetic_manifest(
        exposures={
            f"exposure.my_project.{name}": _exposure_props(name, kind)
            for name, kind in [
                ("d", "dashboard"),
                ("n", "notebook"),
                ("a", "analysis"),
                ("m", "ml"),
                ("app", "application"),
            ]
        }
    )
    specs = build_dbt_exposure_asset_specs(manifest=manifest)
    kinds_by_name = {str(spec.key.to_user_string()): spec.kinds for spec in specs}
    assert kinds_by_name["d"] == {"dashboard"}
    assert kinds_by_name["n"] == {"notebook"}
    assert kinds_by_name["a"] == {"analysis"}
    assert kinds_by_name["m"] == {"ml"}
    assert kinds_by_name["app"] == {"application"}


def test_unknown_exposure_type_yields_no_kind() -> None:
    manifest = _synthetic_manifest(
        exposures={"exposure.my_project.weird": _exposure_props("weird", "made_up_type")}
    )
    specs = build_dbt_exposure_asset_specs(manifest=manifest)
    assert specs[0].kinds is None or specs[0].kinds == set()


def test_exposure_has_deps_on_referenced_models() -> None:
    manifest = _synthetic_manifest(
        nodes={
            "model.my_project.customers": _model_props("customers"),
            "model.my_project.orders": _model_props("orders"),
        },
        exposures={
            "exposure.my_project.dash": _exposure_props(
                "dash", upstream_models=["customers", "orders"]
            )
        },
    )
    specs = build_dbt_exposure_asset_specs(manifest=manifest)
    dep_keys = {dep.asset_key for dep in specs[0].deps}
    assert dep_keys == {AssetKey("customers"), AssetKey("orders")}


def test_exposure_metadata_includes_url_type_and_maturity() -> None:
    manifest = _synthetic_manifest(
        exposures={
            "exposure.my_project.dash": _exposure_props(
                "dash",
                exposure_type="dashboard",
                url="https://tableau.example.com/dash",
                maturity="high",
            )
        }
    )
    spec = build_dbt_exposure_asset_specs(manifest=manifest)[0]
    assert spec.metadata[DAGSTER_DBT_EXPOSURE_TYPE_METADATA_KEY] == "dashboard"
    assert (
        spec.metadata[DAGSTER_DBT_EXPOSURE_URL_METADATA_KEY] == "https://tableau.example.com/dash"
    )
    assert spec.metadata[DAGSTER_DBT_EXPOSURE_MATURITY_METADATA_KEY] == "high"


def test_exposure_url_and_maturity_omitted_when_missing() -> None:
    manifest = _synthetic_manifest(
        exposures={"exposure.my_project.dash": _exposure_props("dash", url=None, maturity=None)}
    )
    metadata = build_dbt_exposure_asset_specs(manifest=manifest)[0].metadata
    assert DAGSTER_DBT_EXPOSURE_URL_METADATA_KEY not in metadata
    assert DAGSTER_DBT_EXPOSURE_MATURITY_METADATA_KEY not in metadata


def test_exposure_description_owner_tags() -> None:
    manifest = _synthetic_manifest(
        exposures={
            "exposure.my_project.dash": _exposure_props(
                "dash",
                description="team dashboard",
                owner_email="team@example.com",
                tags=["priority", "audited"],
            )
        }
    )
    spec = build_dbt_exposure_asset_specs(manifest=manifest)[0]
    assert spec.description == "team dashboard"
    assert spec.owners == ["team@example.com"]
    assert "priority" in spec.tags
    assert "audited" in spec.tags


def test_exposure_with_missing_upstream_skips_that_dep() -> None:
    # Dep on a model that doesn't exist in the manifest should be silently skipped, not raise.
    manifest = _synthetic_manifest(
        nodes={"model.my_project.customers": _model_props("customers")},
        exposures={
            "exposure.my_project.dash": _exposure_props(
                "dash", upstream_models=["customers", "does_not_exist"]
            )
        },
    )
    spec = build_dbt_exposure_asset_specs(manifest=manifest)[0]
    dep_keys = {dep.asset_key for dep in spec.deps}
    assert dep_keys == {AssetKey("customers")}


def test_exposure_asset_key_respects_meta_dagster_override() -> None:
    exposure = _exposure_props("dash")
    exposure["meta"] = {"dagster": {"asset_key": ["custom", "path"]}}
    manifest = _synthetic_manifest(exposures={"exposure.my_project.dash": exposure})
    spec = build_dbt_exposure_asset_specs(manifest=manifest)[0]
    assert spec.key == AssetKey(["custom", "path"])


def test_custom_translator_applies() -> None:
    # A translator subclass overriding get_asset_key should be respected by
    # build_dbt_exposure_asset_specs.
    class PrefixTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props):
            base = super().get_asset_key(dbt_resource_props)
            if dbt_resource_props.get("resource_type") == "exposure":
                return AssetKey(["exposures", *base.path])
            return base

    manifest = _synthetic_manifest(exposures={"exposure.my_project.dash": _exposure_props("dash")})
    spec = build_dbt_exposure_asset_specs(
        manifest=manifest, dagster_dbt_translator=PrefixTranslator()
    )[0]
    assert spec.key == AssetKey(["exposures", "dash"])
