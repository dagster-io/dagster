import re
import sys
import time
from typing import Any

import pytest
from dagster import Config, RunConfig, config_mapping, job, op
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.test_utils import environ, instance_for_test
from dagster._utils.error import serializable_error_info_from_exc_info

from dagster_tests.api_tests.utils import get_bar_repo_handle


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
    with environ({"DAGSTER_REDACT_USER_CODE_ERRORS": "1"}):
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
        and step_error.step_failure_data.error.cls_name == "DagsterRedactedUserCodeError"
    )


ERROR_ID_REGEX = r"Error occurred during user code execution, error ID ([a-z0-9\-]+)"


def test_masking_sensor_execution(instance, enable_masking_user_code_errors, capsys) -> None:
    from dagster._api.snapshot_sensor import sync_get_external_sensor_execution_data_ephemeral_grpc

    with get_bar_repo_handle(instance) as repository_handle:
        try:
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_error", None, None, None, None
            )
            assert False, "Should have thrown an DagsterUserCodeProcessError!"
        except DagsterUserCodeProcessError as e:
            assert "womp womp" not in str(e)
            assert "Search in logs for this error ID for more details" in str(e)
            error_id = re.search(ERROR_ID_REGEX, str(e)).group(1)  # type: ignore

            captured_stderr = capsys.readouterr().err
            assert (
                f"Error occurred during user code execution, error ID {error_id}" in captured_stderr
            )
            # assert "Search in logs for this error ID for more details" not in captured_stderr TODO: fix this


def test_masking_schedule_execution(instance, enable_masking_user_code_errors, capsys) -> None:
    from dagster._api.snapshot_schedule import (
        sync_get_external_schedule_execution_data_ephemeral_grpc,
    )

    with get_bar_repo_handle(instance) as repository_handle:
        try:
            sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "schedule_error",
                TimestampWithTimezone(time.time(), "UTC"),
                None,
                None,
            )
            assert False, "Should have thrown an DagsterUserCodeProcessError!"
        except DagsterUserCodeProcessError as e:
            assert "womp womp" not in str(e)
            assert "Search in logs for this error ID for more details" in str(e)
            error_id = re.search(ERROR_ID_REGEX, str(e)).group(1)  # type: ignore

            captured_stderr = capsys.readouterr().err
            assert (
                f"Error occurred during user code execution, error ID {error_id}" in captured_stderr
            )
            # assert "Search in logs for this error ID for more details" not in captured_stderr TODO: fix this


def test_config_mapping_error(enable_masking_user_code_errors, capsys) -> None:
    class DoSomethingConfig(Config):
        config_param: str

    @op
    def do_something(config: DoSomethingConfig) -> str:
        return config.config_param

    class ConfigMappingConfig(Config):
        simplified_param: str

    # New, fancy config mapping takes in a Pythonic config object and returns a RunConfig
    @config_mapping
    def simplified_config(config_in: ConfigMappingConfig) -> RunConfig:
        if config_in.simplified_param != "foo":
            raise Exception("my password is hunter2")
        return RunConfig(
            ops={"do_something": DoSomethingConfig(config_param=config_in.simplified_param)}
        )

    @job(config=simplified_config)
    def do_it_all_with_simplified_config() -> None:
        do_something()

    result = do_it_all_with_simplified_config.execute_in_process(
        raise_on_error=False, run_config={"simplified_param": "foo"}
    )
    assert result.success

    err_info = None

    try:
        result = do_it_all_with_simplified_config.execute_in_process(
            raise_on_error=False, run_config={"simplified_param": "bar"}
        )
    except Exception:
        # serialize, as in get_external_execution_plan_snapshot (which wraps config mapping execution)
        err_info = serializable_error_info_from_exc_info(sys.exc_info())

    assert err_info
    assert err_info.cls_name == "DagsterRedactedUserCodeError"
    assert "hunter2" not in str(err_info.message)
    assert "Search in logs for this error ID for more details" in str(err_info.message)

    captured_stderr = capsys.readouterr().err
    assert "hunter2" in captured_stderr
