from dagster.components.definitions import LazyDefinitions
from dagster.components.lib.shim_components.resources import ResourcesScaffolder

from dagster_tests.components_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
    make_test_scaffold_request,
)


def test_resources_scaffolder():
    """Test that the ResourcesScaffolder creates valid Python code that evaluates to a Definitions object."""
    scaffolder = ResourcesScaffolder()
    defs_fn = execute_scaffolder_and_get_symbol(scaffolder, "resources")

    # Verify that the object is a valid Definitions object
    assert isinstance(defs_fn, LazyDefinitions)
    assert defs_fn().resources == {}


def test_resources_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = ResourcesScaffolder()
    request = make_test_scaffold_request("resources")
    code = scaffolder.get_text(request)
    execute_ruff_compliance_test(code)
