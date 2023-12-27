import re
from typing import Any

import pytest
from dagster import job, op
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.test_utils import environ, instance_for_test
from dagster._seven import get_current_datetime_in_utc

from ..api_tests.utils import get_bar_repo_handle


@pytest.fixture()
def instance():
    with instance_for_test() as instance:
        yield instance


class UserError(Exception):
    def __init__(self):
        super(UserError, self).__init__(
            "This is an error which has some sensitive information! My password is hunter2"
        )


@pytest.fixture(scope="function")
def enable_masking_user_code_errors() -> Any:
    with environ({"DAGSTER_MASK_USER_CODE_ERRORS": "1"}):
        yield


def test_masking_op_execution(enable_masking_user_code_errors) -> Any:
    @op
    def throws_user_error(_):
        raise UserError()

    @job
    def job_def():
        throws_user_error()

    result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success
    assert not any("hunter2" in str(event) for event in result.all_events)
    step_error = next(event for event in result.all_events if event.is_step_failure)
    assert (
        step_error.step_failure_data.error
        and step_error.step_failure_data.error.cls_name == "DagsterMaskedUserCodeError"
    )


ERROR_ID_REGEX = r"Error occurred during user code execution, error ID ([a-z0-9\-]+)"


def test_masking_sensor_execution(instance, enable_masking_user_code_errors, capsys):
    from dagster._api.snapshot_sensor import (
        sync_get_external_sensor_execution_data_ephemeral_grpc,
    )

    with get_bar_repo_handle(instance) as repository_handle:
        try:
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_error", None, None, None, None
            )
            assert False, "Should have thrown an DagsterUserCodeProcessError!"
        except DagsterUserCodeProcessError as e:
            assert "womp womp" not in str(e)
            assert "Search in logs for this error ID for more details" in str(e)
            error_id = re.search(ERROR_ID_REGEX, str(e)).group(1)

            captured_stderr = capsys.readouterr().err
            assert (
                f"Error occurred during user code execution, error ID {error_id}" in captured_stderr
            )
            # assert "Search in logs for this error ID for more details" not in captured_stderr TODO: fix this


def test_masking_schedule_execution(instance, enable_masking_user_code_errors, capsys):
    from dagster._api.snapshot_schedule import (
        sync_get_external_schedule_execution_data_ephemeral_grpc,
    )

    with get_bar_repo_handle(instance) as repository_handle:
        try:
            sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "schedule_error",
                get_current_datetime_in_utc(),
                None,
                None,
            )
            assert False, "Should have thrown an DagsterUserCodeProcessError!"
        except DagsterUserCodeProcessError as e:
            assert "womp womp" not in str(e)
            assert "Search in logs for this error ID for more details" in str(e)
            error_id = re.search(ERROR_ID_REGEX, str(e)).group(1)

            captured_stderr = capsys.readouterr().err
            assert (
                f"Error occurred during user code execution, error ID {error_id}" in captured_stderr
            )
            # assert "Search in logs for this error ID for more details" not in captured_stderr TODO: fix this
