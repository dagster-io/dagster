import importlib
from pathlib import Path

from dagster import AssetSpec, AutomationCondition
from dagster.components.core.load_defs import load_defs
from dagster.components.core.tree import ComponentTree


def test_custom_scope() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.resolution_tests.custom_scope_component"
    )
    defs = load_defs(module, project_root=Path(__file__).parent)

    assets = list(defs.assets or [])
    assert len(assets) == 1
    spec = assets[0]
    assert isinstance(spec, AssetSpec)

    assert spec.group_name == "xyz"
    assert spec.tags == {"a": "b"}
    assert spec.metadata.get("prefixed") == "prefixed_a|xyz"
    assert (
        spec.automation_condition
        == AutomationCondition.cron_tick_passed("@daily") & ~AutomationCondition.in_progress()
    )


def test_asset_attr():
    from dagster_tests.components_tests.resolution_tests.custom_scope_component.component import (
        HasCustomScope,
    )

    c = HasCustomScope.resolve_from_yaml("""
asset_attributes:
  tags:
    foo: ''
""")

    defs = c.build_defs(ComponentTree.for_test().decl_load_context)
    assert defs.assets
