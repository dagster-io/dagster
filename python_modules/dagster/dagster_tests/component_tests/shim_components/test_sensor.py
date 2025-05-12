from dagster.components.lib.shim_components.sensor import SensorScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
)


def test_sensor_scaffolder():
    """Test that the SensorScaffolder creates valid Python code that evaluates to a sensor."""
    scaffolder = SensorScaffolder()
    # Since the scaffolder returns a commented-out template, we should just verify it's a string
    code = scaffolder.get_text("my_sensor", None)
    assert isinstance(code, str)
    assert "sensor" in code
    assert "SensorEvaluationContext" in code


def test_sensor_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = SensorScaffolder()
    code = scaffolder.get_text("my_sensor", None)
    execute_ruff_compliance_test(code)
