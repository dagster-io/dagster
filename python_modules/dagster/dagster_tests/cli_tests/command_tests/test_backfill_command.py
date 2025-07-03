import string
from contextlib import contextmanager, nullcontext
from typing import Optional

import dagster as dg
import pytest
from click.testing import CliRunner
from dagster._cli.job import execute_backfill_command, job_backfill_command
from dagster._cli.workspace.cli_target import WorkspaceOpts
from dagster._core.instance import DagsterInstance

from dagster_tests.cli_tests.command_tests.test_cli_commands import (
    BackfillCommandTestContext,
    ParsedCliArgs,
    args_with_instance,
    default_cli_test_instance,
    grpc_server_bar_parsed_cli_args,
)


def run_test_backfill(
    parsed_cli_args: ParsedCliArgs,
    instance: DagsterInstance,
    expected_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    with pytest.raises(Exception, match=error_message) if error_message else nullcontext():
        execute_backfill_command(**parsed_cli_args, print_fn=print, instance=instance)
        if expected_count:
            assert instance.get_runs_count() == expected_count


@contextmanager
def _grpc_server_backfill_context():
    with (
        default_cli_test_instance() as instance,
        grpc_server_bar_parsed_cli_args(instance) as cli_args,
    ):
        yield {**cli_args, "noprompt": True}, instance


# This iterates over a list of contextmanagers that can be used to contruct
# (cli_args, instance) tuples for backfill calls
def _backfill_contexts():
    repo_args = {
        "noprompt": True,
        "workspace_opts": WorkspaceOpts(
            workspace=(dg.file_relative_path(__file__, "repository_file.yaml"),)
        ),
    }
    return [
        args_with_instance(default_cli_test_instance(), repo_args),
        _grpc_server_backfill_context(),
    ]


# ########################
# ##### TESTS
# ########################


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_missing_job(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "nonexistent"},
            instance,
            error_message='Job "nonexistent" not found',
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_unpartitioned_job(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "foo"},
            instance,
            error_message="is not partitioned",
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_partitioned_job(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "partitioned_job"}, instance, expected_count=len(string.digits)
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_error_partition_config(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "baz_error_config"},
            instance,
            error_message="Backfill failed",
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_launch(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "baz"}, instance, expected_count=len(string.digits)
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_partition_range(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "baz", "start_partition": "7"}, instance, expected_count=3
        )
        run_test_backfill(
            {**cli_args, "job_name": "baz", "end_partition": "2"}, instance, expected_count=6
        )  # 3 more runs
        run_test_backfill(
            {**cli_args, "job_name": "baz", "start_partition": "2", "end_partition": "5"},
            instance,
            expected_count=10,
        )  # 4 more runs


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_partition_enum(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "job_name": "baz", "partitions": "2,9,0"}, instance, expected_count=3
        )


@pytest.mark.parametrize("backfill_context", _backfill_contexts())
def test_backfill_tags_job(backfill_context: BackfillCommandTestContext):
    with backfill_context as (cli_args, instance):
        run_test_backfill(
            {**cli_args, "partitions": "2", "tags": '{ "foo": "bar" }', "job_name": "baz"},
            instance,
            expected_count=1,
        )
        runs = instance.get_runs()
        run = runs[0]
        assert len(run.tags) >= 1
        assert run.tags.get("foo") == "bar"


def valid_remote_job_backfill_cli_args():
    qux_job_args = [
        "-w",
        dg.file_relative_path(__file__, "repository_file.yaml"),
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


@pytest.mark.parametrize("cli_args", valid_remote_job_backfill_cli_args())
def test_job_backfill_command_cli(cli_args):
    with dg.instance_for_test():
        runner = CliRunner()

        result = runner.invoke(job_backfill_command, cli_args)
        assert result.exit_code == 0
