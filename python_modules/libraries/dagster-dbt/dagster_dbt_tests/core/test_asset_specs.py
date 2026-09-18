import copy
from collections.abc import Mapping, Sequence
from typing import Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_dbt.asset_specs import build_dbt_asset_specs
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


def test_build_dbt_asset_specs_as_external_assets(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    assert Definitions(assets=build_dbt_asset_specs(manifest=test_jaffle_shop_manifest))


def test_build_dbt_asset_specs_with_missing_child_map(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    """Manifests produced by early versions of dbt Fusion do not contain a child map.

    Building asset specs from such a manifest should fall back to building the child map, not crash during selection.
    """
    manifest = copy.deepcopy(test_jaffle_shop_manifest)
    manifest["metadata"]["dbt_version"] = "2.0.0"
    del manifest["child_map"]

    baseline: Sequence[AssetSpec] = build_dbt_asset_specs(manifest=test_jaffle_shop_manifest)
    specs: Sequence[AssetSpec] = build_dbt_asset_specs(manifest=manifest)

    assert [spec.key for spec in specs] == [spec.key for spec in baseline]
    assert [spec.deps for spec in specs] == [spec.deps for spec in baseline]


def test_build_dbt_asset_specs_preserves_translator_attributes(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    class Translator(DagsterDbtTranslator):
        def get_code_version(self, dbt_resource_props: Mapping[str, Any]) -> str | None:
            return "v1"

        def get_automation_condition(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> AutomationCondition | None:
            return AutomationCondition.eager()

    specs = build_dbt_asset_specs(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=Translator(),
    )

    assert Definitions(assets=specs)
    assert all(spec.code_version == "v1" for spec in specs)
    assert all(spec.automation_condition == AutomationCondition.eager() for spec in specs)
