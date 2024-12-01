from dagster._components.impls.pipes_subprocess_script_collection import (
    AutomationConditionInterpreter,
)
from dagster_dbt.asset_utils import AutomationCondition


def test_allowed_operations() -> None:
    operations = AutomationConditionInterpreter.allowed_operations()
    assert "eager" in operations
    assert "requires_cursor" not in operations


def test_interpret_eager() -> None:
    condition = AutomationConditionInterpreter.eval("eager()")
    assert condition.get_label() == "eager"


def test_using_since() -> None:
    condition = AutomationConditionInterpreter.eval(
        "code_version_changed().since(newly_requested())"
    )
    assert isinstance(condition, AutomationCondition)


def test_using_or() -> None:
    condition = AutomationConditionInterpreter.eval(
        "newly_requested() | newly_updated() | initial_evaluation()"
    )
    assert isinstance(condition, AutomationCondition)


def test_with_label() -> None:
    condition = AutomationConditionInterpreter.eval("eager().with_label('test')")
    assert condition.get_label() == "test"
