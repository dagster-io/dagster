from pathlib import Path

from dagster import AssetSpec, AutomationCondition
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.load_defs import load_project_defs


def test_custom_scope() -> None:
    defs = load_project_defs(Path(__file__).parent / "custom_scope_component")

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

    defs = c.build_defs(ComponentLoadContext.for_test())
    assert defs.assets
