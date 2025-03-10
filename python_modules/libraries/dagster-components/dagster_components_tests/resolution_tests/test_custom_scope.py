import importlib

from dagster import AssetSpec, AutomationCondition
from dagster_components.core.component_defs_builder import build_defs_from_component_module


def test_custom_scope() -> None:
    module = importlib.import_module(
        "dagster_components_tests.resolution_tests.custom_scope_component"
    )
    defs = build_defs_from_component_module(
        module=module,
        resources={},
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
