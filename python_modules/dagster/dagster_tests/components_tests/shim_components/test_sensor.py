from dagster.components.lib.shim_components.sensor import SensorScaffolder

from dagster_tests.components_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    make_test_scaffold_request,
)


def test_sensor_scaffolder():
    """Test that the SensorScaffolder creates valid Python code that evaluates to a sensor."""
    scaffolder = SensorScaffolder()
    request = make_test_scaffold_request("my_sensor")
    code = scaffolder.get_text(request)
    assert isinstance(code, str)
    assert "sensor" in code
    assert "SensorEvaluationContext" in code


def test_sensor_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = SensorScaffolder()
    request = make_test_scaffold_request("my_sensor")
    code = scaffolder.get_text(request)
    execute_ruff_compliance_test(code)
