# pylint: disable=unused-argument

import os
import sys
import time
from contextlib import contextmanager
from unittest import mock

import pytest
from click.testing import CliRunner
from dagster import check
from dagster.utils import file_relative_path
from dagster_celery.cli import main


def assert_called(mck):
    if hasattr(mck, "assert_called"):
        mck.assert_called()
    else:
        # py35
        assert mck.called


@contextmanager
def pythonpath(path):
    """Inserts a path into the PYTHONPATH, then restores the previous PYTHONPATH when it
    cleans up"""
    unset = "PYTHONPATH" not in os.environ
    old_path = os.environ.get("PYTHONPATH", "")
    old_sys_path = sys.path
    try:
        os.environ["PYTHONPATH"] = "{old_path}{path}:".format(old_path=old_path, path=path)
        sys.path.insert(0, path)
        yield
    finally:
        if unset:
            del os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = old_path
        sys.path = old_sys_path


def start_worker(name, args=None, exit_code=0, exception_str=""):
    args = check.opt_list_param(args, "args")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["worker", "start", "-A", "dagster_celery.app", "-d", "--name", name] + args,
    )
    assert result.exit_code == exit_code, str(result.exception)
    if exception_str:
        assert exception_str in str(result.exception)


@contextmanager
def cleanup_worker(name, args=None):
    args = check.opt_list_param(args, "args")
    try:
        yield
    finally:
        runner = CliRunner()
        result = runner.invoke(main, ["worker", "terminate", name] + args)
        assert result.exit_code == 0, str(result.exception)


def check_for_worker(name, args=None, present=True):
    runner = CliRunner()
    args = check.opt_list_param(args, "args")
    result = runner.invoke(main, ["worker", "list"] + args)
    assert result.exit_code == 0, str(result.exception)
    retry_count = 0
    while retry_count < 10 and (
        not "{name}@".format(name=name) in result.output
        if present
        else "{name}@".format(name=name) in result.output
    ):
        time.sleep(1)
        result = runner.invoke(main, ["worker", "list"] + args)
        assert result.exit_code == 0, str(result.exception)
        retry_count += 1
    return (
        "{name}@".format(name=name) in result.output
        if present
        else "{name}@".format(name=name) not in result.output
    )


def test_invoke_entrypoint():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "worker" in result.output

    runner = CliRunner()
    result = runner.invoke(main, ["worker"])
    assert result.exit_code == 0
    assert "Start a dagster celery worker" in result.output


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker(rabbitmq):
    with cleanup_worker("dagster_test_worker"):
        start_worker("dagster_test_worker")
        assert check_for_worker("dagster_test_worker")


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker_too_many_queues(rabbitmq):
    args = ["-q", "1", "-q", "2", "-q", "3", "-q", "4", "-q", "5"]

    with cleanup_worker("dagster_test_worker"):
        start_worker(
            "dagster_test_worker",
            args=args,
            exit_code=1,
            exception_str=(
                "Can't start a dagster_celery worker that listens on more than four queues, due to a "
                "bug in Celery 4."
            ),
        )


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker_addargs(rabbitmq):
    args = ["--", "--uid", "42"]

    # Omitting check that uid is actually 42 to avoid a heavy test dependency on psutil
    with cleanup_worker("dagster_test_worker"):
        start_worker(
            "dagster_test_worker",
            args=args,
        )


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker_config_from_empty_yaml(rabbitmq):
    args = ["-y", file_relative_path(__file__, "empty.yaml")]
    with cleanup_worker("dagster_test_worker", args=args):
        start_worker("dagster_test_worker", args=args)
        assert check_for_worker("dagster_test_worker", args=args)


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker_config_from_partial_yaml(rabbitmq):
    args = ["-y", file_relative_path(__file__, "partial.yaml")]
    with cleanup_worker("dagster_test_worker", args=args):
        start_worker("dagster_test_worker", args=args)
        assert check_for_worker("dagster_test_worker", args=args)


# https://github.com/dagster-io/dagster/issues/3494
@pytest.mark.skip
def test_start_worker_config_from_yaml(rabbitmq):
    args = ["-y", file_relative_path(__file__, "engine_config.yaml")]

    with cleanup_worker("dagster_test_worker", args=args):
        start_worker("dagster_test_worker", args=args)
        assert check_for_worker("dagster_test_worker", args=args)


@mock.patch("dagster_celery.cli.launch_background_worker")
def test_mock_start_worker(worker_patch):
    start_worker("dagster_test_worker")
    assert_called(worker_patch)


@mock.patch("dagster_celery.cli.launch_background_worker")
def test_mock_start_worker_config_from_empty_yaml(worker_patch):
    args = ["-y", file_relative_path(__file__, "empty.yaml")]
    start_worker("dagster_test_worker", args=args)
    assert_called(worker_patch)


@mock.patch("dagster_celery.cli.launch_background_worker")
def test_start_mock_worker_config_from_yaml(worker_patch):
    args = ["-y", file_relative_path(__file__, "engine_config.yaml")]
    start_worker("dagster_test_worker", args=args)
    assert_called(worker_patch)


@mock.patch("dagster_celery.cli.launch_background_worker")
def test_mock_start_worker_too_many_queues(_worker_patch):
    args = ["-q", "1", "-q", "2", "-q", "3", "-q", "4", "-q", "5"]

    start_worker(
        "dagster_test_worker",
        args=args,
        exit_code=1,
        exception_str=(
            "Can't start a dagster_celery worker that listens on more than four queues, due to a "
            "bug in Celery 4."
        ),
    )
