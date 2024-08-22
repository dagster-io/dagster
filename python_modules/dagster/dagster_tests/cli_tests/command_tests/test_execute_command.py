import os
import re

import click
import pytest
from click import UsageError
from click.testing import CliRunner
from dagster._cli.job import execute_execute_command, job_execute_command
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.test_utils import instance_for_test, new_cwd
from dagster._utils import file_relative_path
from dagster._utils.merger import merge_dicts

from dagster_tests.cli_tests.command_tests.test_cli_commands import (
    job_python_origin_contexts,
    non_existant_python_origin_target_args,
    runner_job_execute,
    valid_job_python_origin_target_cli_args,
)


def test_execute_with_config_command():
    runner = CliRunner()

    with instance_for_test():
        add_result = runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/adder_job.yaml"),
                "-j",
                "adder_job",  # job name
            ],
        )

        assert add_result

        mult_result = runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/multer_job.yaml"),
                "-j",
                "multer_job",  # job name
            ],
        )

        assert mult_result

        double_adder_result = runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/double_adder_job.yaml"),
                "-j",
                "double_adder_job",  # job name
            ],
        )

        assert double_adder_result


def test_empty_execute_command():
    with instance_for_test():
        runner = CliRunner()

        result = runner.invoke(job_execute_command, [])
        assert result.exit_code == 2
        assert "Must specify a python file or module name" in result.output


@pytest.mark.parametrize("gen_execute_args", job_python_origin_contexts())
def test_execute_command_no_env(gen_execute_args):
    with gen_execute_args as (cli_args, instance):
        execute_execute_command(kwargs=cli_args, instance=instance)


@pytest.mark.parametrize("gen_execute_args", job_python_origin_contexts())
def test_job_execute_command_no_env(gen_execute_args):
    with gen_execute_args as (cli_args, instance):
        execute_execute_command(kwargs=cli_args, instance=instance)


@pytest.mark.parametrize("gen_execute_args", job_python_origin_contexts())
def test_execute_command_env(gen_execute_args):
    with gen_execute_args as (cli_args, instance):
        kwargs = merge_dicts(
            {"config": (file_relative_path(__file__, "default_log_error_env.yaml"),)},
            cli_args,
        )
        execute_execute_command(
            kwargs=kwargs,
            instance=instance,
        )


@pytest.mark.parametrize("gen_execute_args", job_python_origin_contexts())
def test_job_execute_command_env(gen_execute_args):
    with gen_execute_args as (cli_args, instance):
        kwargs = merge_dicts(
            {"config": (file_relative_path(__file__, "default_log_error_env.yaml"),)},
            cli_args,
        )
        execute_execute_command(
            kwargs=kwargs,
            instance=instance,
        )


@pytest.mark.parametrize("cli_args", valid_job_python_origin_target_cli_args())
def test_job_execute_command_runner(cli_args):
    runner = CliRunner()
    with instance_for_test():
        runner_job_execute(runner, cli_args)

        runner_job_execute(
            runner,
            ["--config", file_relative_path(__file__, "default_log_error_env.yaml")] + cli_args,
        )


def test_output_execute_log_stdout(capfd):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        execute_execute_command(
            kwargs={
                "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                "attribute": "stdout_job",
            },
            instance=instance,
        )

        captured = capfd.readouterr()
        # All job execution output currently logged to stderr
        assert "HELLO WORLD" in captured.err

        execute_execute_command(
            kwargs={
                "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                "attribute": "my_stdout",
            },
            instance=instance,
        )

        captured = capfd.readouterr()
        assert "SPEW OP" in captured.err


def test_output_execute_log_stderr(capfd):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        with pytest.raises(click.ClickException, match=re.escape("resulted in failure")):
            execute_execute_command(
                kwargs={
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "attribute": "stderr_job",
                },
                instance=instance,
            )
        captured = capfd.readouterr()
        assert "I AM SUPPOSED TO FAIL" in captured.err

        with pytest.raises(click.ClickException, match=re.escape("resulted in failure")):
            execute_execute_command(
                kwargs={
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "attribute": "my_stderr",
                },
                instance=instance,
            )
        captured = capfd.readouterr()
        assert "FAILURE OP" in captured.err


def test_more_than_one_job():
    with instance_for_test() as instance:
        with pytest.raises(
            UsageError,
            match=re.escape("Must provide --job as there is more than one job in bar"),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "job_name": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": None,
                },
                instance=instance,
            )

        with pytest.raises(
            UsageError,
            match=re.escape("Must provide --job as there is more than one job in bar. "),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "job_name": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": None,
                },
                instance=instance,
            )


def invalid_pipeline_python_origin_target_args():
    return [
        {
            "job_name": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "job_name": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": None,
        },
    ]


@pytest.mark.parametrize("args", invalid_pipeline_python_origin_target_args())
def test_invalid_parameters(args):
    with instance_for_test() as instance:
        with pytest.raises(
            UsageError,
            match=re.escape("Invalid set of CLI arguments for loading repository/job"),
        ):
            execute_execute_command(
                kwargs=args,
                instance=instance,
            )


def test_execute_non_existant_file():
    with instance_for_test() as instance:
        kwargs = non_existant_python_origin_target_args()

        with pytest.raises(OSError):
            execute_execute_command(kwargs=kwargs, instance=instance)


def test_attribute_not_found():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape("nope not found at module scope in file"),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "job_name": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": "nope",
                },
                instance=instance,
            )


def test_attribute_is_wrong_thing():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape(
                "Loadable attributes must be either a JobDefinition, GraphDefinition,"
                " or RepositoryDefinition. Got 123."
            ),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "job_name": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": "not_a_repo_or_job",
                },
                instance=instance,
            )


def test_attribute_fn_returns_wrong_thing():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape(
                "Loadable attributes must be either a JobDefinition, GraphDefinition,"
                " or RepositoryDefinition."
            ),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "job_name": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": "not_a_repo_or_job_fn",
                },
                instance=instance,
            )


def test_default_memory_run_storage():
    with instance_for_test() as instance:
        cli_args = {
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "attribute": "bar",
            "job_name": "foo",
            "module_name": None,
        }
        result = execute_execute_command(kwargs=cli_args, instance=instance)
        assert result.success

        cli_args = {
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "attribute": "bar",
            "job_name": "qux",
            "module_name": None,
        }
        result = execute_execute_command(kwargs=cli_args, instance=instance)
        assert result.success


def test_multiproc():
    with instance_for_test():
        runner = CliRunner()
        add_result = runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(__file__, "../../environments/adder_job.yaml"),
                "-j",
                "multi_job",  # job name
            ],
        )
        assert add_result.exit_code == 0

        assert "RUN_SUCCESS" in add_result.output

        add_result = runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "multiproc",
            ],
        )
        assert add_result.exit_code == 0

        assert "RUN_SUCCESS" in add_result.output


def test_tags_job():
    runner = CliRunner()
    with instance_for_test() as instance:
        result = runner.invoke(
            job_execute_command,
            [
                "-m",
                "dagster_tests.cli_tests.command_tests.test_cli_commands",
                "-a",
                "bar",
                "--tags",
                '{ "foo": "bar" }',
                "-j",
                "qux",
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get("foo") == "bar"

    with instance_for_test() as instance:
        result = runner.invoke(
            job_execute_command,
            [
                "-m",
                "dagster_tests.cli_tests.command_tests.test_cli_commands",
                "-a",
                "bar",
                "--tags",
                '{ "foo": "bar" }',
                "-j",
                "qux",
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get("foo") == "bar"

    with instance_for_test() as instance:
        result = runner.invoke(
            job_execute_command,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--tags",
                '{ "foo": "bar" }',
                "--config",
                file_relative_path(__file__, "../../environments/adder_job.yaml"),
                "-j",
                "adder_job",  # job name
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get("foo") == "bar"


def test_empty_working_directory():
    runner = CliRunner()

    with instance_for_test() as instance:
        with new_cwd(os.path.dirname(__file__)):
            result = runner.invoke(
                job_execute_command,
                [
                    "-f",
                    file_relative_path(__file__, "file_with_local_import.py"),
                    "-a",
                    "qux_job",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1


def test_execute_command_help():
    runner = CliRunner()
    result = runner.invoke(job_execute_command, ["--help"])

    assert "multiple times" not in result.stdout


def test_op_selection():
    runner = CliRunner()
    with instance_for_test() as instance:
        runner_job_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-j",
                "foo",
                "--op-selection",
                "*do_something",
            ],
        )

        runs = instance.get_run_records()
        assert len(runs) == 1
        conn = instance.get_records_for_run(run_id=runs[0].dagster_run.run_id)
        observed_steps = {record.event_log_entry.step_key for record in conn.records}
        assert "do_something" in observed_steps
        assert "do_input" not in observed_steps
