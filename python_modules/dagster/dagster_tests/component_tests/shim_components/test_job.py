from dagster import JobDefinition
from dagster.components.lib.shim_components.job import JobScaffolder
from dagster_tests.component_tests.shim_components.shim_test_utils import (
    execute_ruff_compliance_test,
    execute_scaffolder_and_get_symbol,
)


def test_job_scaffolder():
    """Test that the JobScaffolder creates valid Python code that evaluates to a job."""
    scaffolder = JobScaffolder()
    job_fn = execute_scaffolder_and_get_symbol(scaffolder, "my_job")

    # Verify that the function creates a valid job
    assert isinstance(job_fn, JobDefinition)


def test_job_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    scaffolder = JobScaffolder()
    code = scaffolder.get_text("my_job", None)
    execute_ruff_compliance_test(code)
