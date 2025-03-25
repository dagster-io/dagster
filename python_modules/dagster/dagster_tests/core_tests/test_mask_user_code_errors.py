import logging
import re
import sys
import time
import traceback
from typing import Any, Callable

import pytest
from dagster import Config, RunConfig, config_mapping, job, op
from dagster._core.definitions.events import Failure
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterUserCodeExecutionError,
    DagsterUserCodeProcessError,
    user_code_error_boundary,
)
from dagster._core.test_utils import environ, instance_for_test
from dagster._utils.error import (
    _serializable_error_info_from_tb,
    serializable_error_info_from_exc_info,
)

from dagster_tests.api_tests.utils import get_bar_repo_handle


@pytest.fixture()
def instance():
    with instance_for_test() as instance:
        yield instance


class UserError(Exception):
    def __init__(self):
        super().__init__(
            "This is an error which has some sensitive information! My password is hunter2"
        )


class hunter2:
    pass


@pytest.fixture(scope="function")
def enable_masking_user_code_errors() -> Any:
    with environ({"DAGSTER_REDACT_USER_CODE_ERRORS": "1"}):
        yield


def test_masking_basic(enable_masking_user_code_errors):
    try:
        with user_code_error_boundary(
            error_cls=DagsterUserCodeExecutionError,
            msg_fn=lambda: "hunter2",
        ):

            def hunter2():
                raise UserError()

            hunter2()
    except Exception:
        exc_info = sys.exc_info()
        err_info = serializable_error_info_from_exc_info(exc_info)

    assert "hunter2" not in str(err_info)  # pyright: ignore[reportPossiblyUnboundVariable]


def test_masking_nested_user_code_err_boundaries(enable_masking_user_code_errors):
    try:
        with user_code_error_boundary(
            error_cls=DagsterUserCodeExecutionError,
            msg_fn=lambda: "hunter2 as well",
        ):
            with user_code_error_boundary(
                error_cls=DagsterUserCodeExecutionError,
                msg_fn=lambda: "hunter2",
            ):

                def hunter2():
                    raise UserError()

                hunter2()
    except Exception:
        exc_info = sys.exc_info()
        err_info = serializable_error_info_from_exc_info(exc_info)

    assert "hunter2" not in str(err_info)  # pyright: ignore[reportPossiblyUnboundVariable]


def test_masking_nested_user_code_err_boundaries_reraise(enable_masking_user_code_errors):
    try:
        try:
            with user_code_error_boundary(
                error_cls=DagsterUserCodeExecutionError,
                msg_fn=lambda: "hunter2",
            ):

                def hunter2():
                    raise UserError()

                hunter2()
        except Exception as e:
            # Mimics behavior of resource teardown, which runs in a
            # user_code_error_boundary after the user code raises an error
            with user_code_error_boundary(
                error_cls=DagsterUserCodeExecutionError,
                msg_fn=lambda: "teardown after we raised hunter2 error",
            ):
                # do teardown stuff
                raise e

    except Exception:
        exc_info = sys.exc_info()
        err_info = serializable_error_info_from_exc_info(exc_info)

    assert "hunter2" not in str(err_info)  # pyright: ignore[reportPossiblyUnboundVariable]


ERROR_ID_REGEX = r"[Ee]rror ID ([a-z0-9\-]+)"


@pytest.mark.parametrize(
    "exc_name, expect_exc_name_in_error, build_exc",
    [
        ("UserError", False, lambda: UserError()),
        ("TypeError", False, lambda: TypeError("hunter2")),
        ("KeyboardInterrupt", True, lambda: KeyboardInterrupt()),
        ("DagsterExecutionInterruptedError", True, lambda: DagsterExecutionInterruptedError()),
        ("Failure", True, lambda: Failure("asdf")),
    ],
)
def test_masking_op_execution(
    enable_masking_user_code_errors,
    exc_name: str,
    expect_exc_name_in_error: bool,
    build_exc: Callable[[], BaseException],
    caplog,
) -> Any:
    @op
    def throws_user_error(_):
        def hunter2():
            raise build_exc()

        hunter2()

    @job
    def job_def():
        throws_user_error()

    with caplog.at_level(logging.ERROR):
        result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success

    # Ensure error message and contents of user code don't leak (e.g. hunter2 text or function name)
    assert not any("hunter2" in str(event).lower() for event in result.all_events), [
        str(event) for event in result.all_events if "hunter2" in str(event)
    ]

    step_error = next(event for event in result.all_events if event.is_step_failure)

    # Certain exceptions will not be fully redacted, just the stack trace
    # For example, system errors and interrupts may contain useful information
    # or information that the framework itself relies on
    if expect_exc_name_in_error:
        assert (
            step_error.step_failure_data.error
            and step_error.step_failure_data.error.cls_name == exc_name
        )
    else:
        assert (
            step_error.step_failure_data.error
            and step_error.step_failure_data.error.cls_name == "DagsterRedactedUserCodeError"
        )

    # Ensures we can match the error ID in the Dagster+ UI surfaced message to the rich error message
    # in logs which includes the redacted error message
    assert "Search in logs for this error ID for more details" in str(step_error)
    error_id = re.search(ERROR_ID_REGEX, str(step_error)).group(1)  # type: ignore

    assert f"Error occurred during user code execution, error ID {error_id}" in caplog.text
    assert "hunter2" in caplog.text


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


def test_config_mapping_error(enable_masking_user_code_errors, caplog) -> None:
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

    assert any(
        "hunter2"
        in str(_serializable_error_info_from_tb(traceback.TracebackException(*record.exc_info)))
        for record in caplog.records
        if record.exc_info
    )
