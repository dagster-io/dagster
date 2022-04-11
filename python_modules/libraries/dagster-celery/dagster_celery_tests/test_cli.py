# pylint: disable=unused-argument

import time

from click.testing import CliRunner
from dagster_celery.cli import main

from dagster import check
from dagster.utils import file_relative_path


def start_worker(name, config_yaml=None, args=None, exit_code=0, exception_str=""):
    args = check.opt_list_param(args, "args")
    runner = CliRunner()

    config_args = ["-y", config_yaml] if config_yaml else []
    try:
        result = runner.invoke(
            main,
            ["worker", "start", "-A", "dagster_celery.app", "-d", "--name", name]
            + config_args
            + args,
        )
        assert result.exit_code == exit_code, str(result.exception)
        if exception_str:
            assert exception_str in str(result.exception)
        else:
            check_for_worker(name, config_args)
    finally:
        result = runner.invoke(main, ["worker", "terminate", name] + config_args)
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


def test_start_worker(rabbitmq, instance):
    start_worker("dagster_test_worker")


def test_start_worker_too_many_queues(rabbitmq, instance):
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


def test_start_worker_config_from_empty_yaml(rabbitmq, instance):
    start_worker("dagster_test_worker", config_yaml=file_relative_path(__file__, "empty.yaml"))


def test_start_worker_config_from_partial_yaml(rabbitmq, instance):
    start_worker("dagster_test_worker", config_yaml=file_relative_path(__file__, "partial.yaml"))


def test_start_worker_config_from_yaml(rabbitmq, instance):
    start_worker(
        "dagster_test_worker", config_yaml=file_relative_path(__file__, "engine_config.yaml")
    )
