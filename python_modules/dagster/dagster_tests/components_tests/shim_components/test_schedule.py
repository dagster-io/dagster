import dagster as dg
from dagster.components.lib.shim_components.schedule import ScheduleScaffolder

from dagster_tests.components_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
    make_test_scaffold_request,
)


def test_schedule_scaffolder():
    """Test that the ScheduleScaffolder creates valid Python code that evaluates to a schedule."""
    scaffolder = ScheduleScaffolder()
    request = make_test_scaffold_request("my_schedule")
    code = scaffolder.get_text(request)
    assert isinstance(code, str)
    assert "schedule" in code
    assert "ScheduleEvaluationContext" in code
    assert "RunRequest" in code

    schedule_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_schedule")
    assert isinstance(schedule_fn, dg.ScheduleDefinition)
    assert schedule_fn.name == "my_schedule"


def test_schedule_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = ScheduleScaffolder()
    request = make_test_scaffold_request("my_schedule")
    code = scaffolder.get_text(request)
    execute_ruff_compliance_test(code)
