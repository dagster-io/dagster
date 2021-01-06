import sys

from dagster.core.errors import DagsterUserCodeExecutionError, user_code_error_boundary
from dagster.core.execution.plan.objects import ErrorSource, StepFailureData
from dagster.utils.error import serializable_error_info_from_exc_info


def test_failure_error_display_string():
    try:
        with user_code_error_boundary(
            DagsterUserCodeExecutionError, lambda: "Error occurred while doing the thing"
        ):
            raise ValueError("some error")
    except DagsterUserCodeExecutionError:
        step_failure_data = StepFailureData(
            error=serializable_error_info_from_exc_info(sys.exc_info()),
            user_failure_data=None,
            error_source=ErrorSource.USER_CODE_ERROR,
        )

        assert step_failure_data.error_display_string.startswith(
            """
dagster.core.errors.DagsterUserCodeExecutionError: Error occurred while doing the thing:

ValueError: some error

Stack Trace:
  File "
""".strip()
        )
