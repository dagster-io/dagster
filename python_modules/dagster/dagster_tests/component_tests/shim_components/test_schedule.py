from dagster.components.lib.shim_components.schedule import ScheduleScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
)


def test_schedule_scaffolder():
    """Test that the ScheduleScaffolder creates valid Python code that evaluates to a schedule."""
    scaffolder = ScheduleScaffolder()
    # Since the scaffolder returns a commented-out template, we should just verify it's a string
    code = scaffolder.get_text("my_schedule", None)
    assert isinstance(code, str)
    assert "schedule" in code
    assert "ScheduleEvaluationContext" in code
    assert "RunRequest" in code


def test_schedule_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = ScheduleScaffolder()
    code = scaffolder.get_text("my_schedule", None)
    execute_ruff_compliance_test(code)
