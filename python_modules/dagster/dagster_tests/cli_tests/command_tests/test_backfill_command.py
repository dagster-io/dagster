import string
from typing import Optional

import pytest
from click.testing import CliRunner
from dagster._cli.job import execute_backfill_command, job_backfill_command
from dagster._cli.workspace.cli_target import ClickArgMapping
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path
from dagster._utils.merger import merge_dicts

from dagster_tests.cli_tests.command_tests.test_cli_commands import (
    BackfillCommandTestContext,
    backfill_command_contexts,
)


def run_test_backfill(
    execution_args: ClickArgMapping,
    instance: DagsterInstance,
    expected_count: Optional[int] = None,
    error_message: Optional[str] = None,
):
    run_test_backfill_inner(execution_args, instance, expected_count, error_message)


def run_test_backfill_inner(
    execution_args: ClickArgMapping,
    instance: DagsterInstance,
    expected_count: Optional[int],
    error_message: Optional[str],
) -> None:
    if error_message:
        with pytest.raises(Exception):
            execute_backfill_command(execution_args, print, instance)
    else:
        execute_backfill_command(execution_args, print, instance)
        if expected_count:
            assert instance.get_runs_count() == expected_count


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_missing_job(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "nonexistent"})
        run_test_backfill(args, instance, error_message="No pipeline or job found")


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_unpartitioned_job(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "foo"})
        run_test_backfill(
            args,
            instance,
            error_message="is not partitioned",
        )


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_partitioned_job(
    backfill_args_context: BackfillCommandTestContext,
):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "partitioned_job"})
        run_test_backfill(args, instance, expected_count=len(string.digits))


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_error_partition_config(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "baz_error_config"})
        run_test_backfill(
            args,
            instance,
            error_message="Backfill failed",
        )


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_launch(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "baz"})
        run_test_backfill(args, instance, expected_count=len(string.digits))


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_partition_range(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(cli_args, {"job_name": "baz", "from": "7"})
        run_test_backfill(args, instance, expected_count=3)

        args = merge_dicts(cli_args, {"job_name": "baz", "to": "2"})
        run_test_backfill(args, instance, expected_count=6)  # 3 more runs

        args = merge_dicts(
            cli_args,
            {"job_name": "baz", "from": "2", "to": "5"},
        )
        run_test_backfill(args, instance, expected_count=10)  # 4 more runs


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_partition_enum(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(
            cli_args,
            {"job_name": "baz", "partition_set": "baz_partitions", "partitions": "2,9,0"},
        )
        run_test_backfill(args, instance, expected_count=3)


@pytest.mark.parametrize("backfill_args_context", backfill_command_contexts())
def test_backfill_tags_job(backfill_args_context: BackfillCommandTestContext):
    with backfill_args_context as (cli_args, instance):
        args = merge_dicts(
            cli_args,
            {
                "partition_set": "baz_partitions",
                "partitions": "2",
                "tags": '{ "foo": "bar" }',
                "job_name": "baz",
            },
        )

        run_test_backfill(args, instance, expected_count=1)

        runs = instance.get_runs()
        run = runs[0]
        assert len(run.tags) >= 1
        assert run.tags.get("foo") == "bar"


def valid_external_job_backfill_cli_args():
    qux_job_args = [
        "-w",
        file_relative_path(__file__, "repository_file.yaml"),
        "-j",
        "qux",
        "--noprompt",
    ]
    return [
        qux_job_args + flag_args
        for flag_args in [
            ["--partitions", "abc"],
            ["--all", "all"],
            ["--from", "abc"],
            ["--to", "abc"],
        ]
    ]


@pytest.mark.parametrize("job_cli_args", valid_external_job_backfill_cli_args())
def test_job_backfill_command_cli(job_cli_args):
    with instance_for_test():
        runner = CliRunner()

        result = runner.invoke(job_backfill_command, job_cli_args)
        assert result.exit_code == 0, result
