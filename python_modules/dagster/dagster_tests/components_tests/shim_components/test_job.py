import dagster as dg
from dagster.components.lib.shim_components.job import JobScaffolder

from dagster_tests.components_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
    make_test_scaffold_request,
)


def test_job_scaffolder():
    """Test that the JobScaffolder creates valid Python code that evaluates to a job."""
    scaffolder = JobScaffolder()
    job_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_job")

    # Verify that the function creates a valid job
    assert isinstance(job_fn, dg.JobDefinition)


def test_job_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = JobScaffolder()
    request = make_test_scaffold_request("my_job")
    code = scaffolder.get_text(request)
    execute_ruff_compliance_test(code)
