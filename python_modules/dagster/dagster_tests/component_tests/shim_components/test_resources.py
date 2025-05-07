from dagster import Definitions
from dagster.components.lib.shim_components.resources import ResourcesScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
)


def test_resources_scaffolder():
    """Test that the ResourcesScaffolder creates valid Python code that evaluates to a Definitions object."""
    scaffolder = ResourcesScaffolder()
    defs_fn = execute_scaffolder_and_get_symbol(scaffolder, "resources")

    # Verify that the function creates a valid Definitions object
    defs = defs_fn()
    assert isinstance(defs, Definitions)
    assert defs.resources == {}


def test_resources_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = ResourcesScaffolder()
    code = scaffolder.get_text("resources", None)
    execute_ruff_compliance_test(code)
