from pathlib import Path

from dagster import AssetSpec, AutomationCondition
from dagster_components.core.component_defs_builder import MultiComponentsLoadContext


def test_custom_scope() -> None:
    defs = MultiComponentsLoadContext(resources={}).build_defs_from_component_path(
        path=Path(__file__).parent / "custom_scope_component",
    )

    assets = list(defs.assets or [])
    assert len(assets) == 1
    spec = assets[0]
    assert isinstance(spec, AssetSpec)

    assert spec.group_name == "xyz"
    assert spec.tags == {"a": "b"}
    assert spec.metadata == {"prefixed": "prefixed_a|xyz"}
    assert (
        spec.automation_condition
        == AutomationCondition.cron_tick_passed("@daily") & ~AutomationCondition.in_progress()
    )
