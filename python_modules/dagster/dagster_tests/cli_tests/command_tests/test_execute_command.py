import os
import re

import click
import pytest
from click import UsageError
from click.testing import CliRunner
from dagster.cli.pipeline import execute_execute_command, pipeline_execute_command
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.test_utils import instance_for_test, new_cwd
from dagster.utils import file_relative_path, merge_dicts

from .test_cli_commands import (
    non_existant_python_origin_target_args,
    pipeline_python_origin_contexts,
    valid_pipeline_python_origin_target_cli_args,
)


def test_execute_mode_command():
    runner = CliRunner()

    with instance_for_test():
        add_result = runner_pipeline_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(
                    __file__, "../../environments/multi_mode_with_resources/add_mode.yaml"
                ),
                "--mode",
                "add_mode",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        assert add_result

        mult_result = runner_pipeline_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(
                    __file__, "../../environments/multi_mode_with_resources/mult_mode.yaml"
                ),
                "--mode",
                "mult_mode",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        assert mult_result

        double_adder_result = runner_pipeline_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                file_relative_path(
                    __file__, "../../environments/multi_mode_with_resources/double_adder_mode.yaml"
                ),
                "--mode",
                "double_adder_mode",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        assert double_adder_result


def test_empty_execute_command():
    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(pipeline_execute_command, [])
        assert result.exit_code == 2
        assert "Must specify a python file or module name" in result.output


def test_execute_preset_command():
    with instance_for_test():
        runner = CliRunner()
        add_result = runner_pipeline_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "add",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )

        assert "PIPELINE_SUCCESS" in add_result.output

        # Can't use --preset with --config
        bad_res = runner.invoke(
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "add",
                "--config",
                file_relative_path(
                    __file__, "../../environments/multi_mode_with_resources/double_adder_mode.yaml"
                ),
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )
        assert bad_res.exit_code == 2


@pytest.mark.parametrize("gen_execute_args", pipeline_python_origin_contexts())
def test_execute_command_no_env(gen_execute_args):
    with gen_execute_args as (cli_args, instance):
        execute_execute_command(kwargs=cli_args, instance=instance)


@pytest.mark.parametrize("gen_execute_args", pipeline_python_origin_contexts())
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


@pytest.mark.parametrize("cli_args", valid_pipeline_python_origin_target_cli_args())
def test_execute_command_runner(cli_args):
    runner = CliRunner()
    with instance_for_test():
        runner_pipeline_execute(runner, cli_args)

        runner_pipeline_execute(
            runner,
            ["--config", file_relative_path(__file__, "default_log_error_env.yaml")] + cli_args,
        )


def test_output_execute_log_stdout(capfd):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster.core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        execute_execute_command(
            kwargs={
                "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                "attribute": "stdout_pipeline",
            },
            instance=instance,
        )

        captured = capfd.readouterr()
        # All pipeline execute output currently logged to stderr
        assert "HELLO WORLD" in captured.err


def test_output_execute_log_stderr(capfd):
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster.core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        with pytest.raises(click.ClickException, match=re.escape("resulted in failure")):
            execute_execute_command(
                kwargs={
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "attribute": "stderr_pipeline",
                },
                instance=instance,
            )
        captured = capfd.readouterr()
        assert "I AM SUPPOSED TO FAIL" in captured.err


def test_more_than_one_pipeline():
    with instance_for_test() as instance:
        with pytest.raises(
            UsageError,
            match=re.escape("Must provide --pipeline as there is more than one pipeline in bar. "),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "pipeline": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": None,
                },
                instance=instance,
            )


def invalid_pipeline_python_origin_target_args():
    return [
        {
            "pipeline": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
        {
            "pipeline": "foo",
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": None,
        },
        {
            "pipeline": "foo",
            "python_file": None,
            "working_directory": os.path.dirname(__file__),
            "module_name": "dagster_tests.cli_tests.command_tests.test_cli_commands",
            "attribute": "bar",
        },
    ]


@pytest.mark.parametrize("args", invalid_pipeline_python_origin_target_args())
def test_invalid_parameters(args):
    with instance_for_test() as instance:
        with pytest.raises(
            UsageError,
            match=re.escape("Invalid set of CLI arguments for loading repository/pipeline"),
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
                    "pipeline": None,
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
                "Loadable attributes must be either a PipelineDefinition or a "
                "RepositoryDefinition. Got 123."
            ),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "pipeline": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": "not_a_repo_or_pipeline",
                },
                instance=instance,
            )


def test_attribute_fn_returns_wrong_thing():
    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvariantViolationError,
            match=re.escape(
                "Loadable attributes must be either a PipelineDefinition or a RepositoryDefinition."
            ),
        ):
            execute_execute_command(
                kwargs={
                    "repository_yaml": None,
                    "pipeline": None,
                    "python_file": file_relative_path(__file__, "test_cli_commands.py"),
                    "module_name": None,
                    "attribute": "not_a_repo_or_pipeline_fn",
                },
                instance=instance,
            )


def runner_pipeline_execute(runner, cli_args):
    result = runner.invoke(pipeline_execute_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster pipeline execute commands with cli_args {cli_args} "
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args, exit_code=result.exit_code, stdout=result.stdout, result=result
            )
        )
    return result


def test_default_memory_run_storage():
    with instance_for_test() as instance:
        cli_args = {
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "atribute": "bar",
            "pipeline": "foo",
            "module_name": None,
        }
        result = execute_execute_command(kwargs=cli_args, instance=instance)
        assert result.success


def test_override_with_in_memory_storage():
    with instance_for_test() as instance:
        cli_args = {
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "atribute": "bar",
            "pipeline": "foo",
            "module_name": None,
            "config": (file_relative_path(__file__, "in_memory_env.yaml"),),
        }
        result = execute_execute_command(
            kwargs=cli_args,
            instance=instance,
        )
        assert result.success


def test_override_with_filesystem_storage():
    with instance_for_test() as instance:
        cli_args = {
            "python_file": file_relative_path(__file__, "test_cli_commands.py"),
            "atribute": "bar",
            "pipeline": "foo",
            "module_name": None,
            "config": (file_relative_path(__file__, "filesystem_env.yaml"),),
        }
        result = execute_execute_command(
            kwargs=cli_args,
            instance=instance,
        )
        assert result.success


def test_multiproc():
    with instance_for_test():
        runner = CliRunner()
        add_result = runner_pipeline_execute(
            runner,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "multiproc",
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )
        assert add_result.exit_code == 0

        assert "PIPELINE_SUCCESS" in add_result.output


def test_multiproc_invalid():
    # force ephemeral instance by removing out DAGSTER_HOME
    runner = CliRunner(env={"DAGSTER_HOME": None})
    add_result = runner.invoke(
        pipeline_execute_command,
        [
            "-f",
            file_relative_path(__file__, "../../general_tests/test_repository.py"),
            "-a",
            "dagster_test_repository",
            "--preset",
            "multiproc",
            "-p",
            "multi_mode_with_resources",  # pipeline name
        ],
    )
    # which is invalid for multiproc
    assert add_result.exit_code != 0
    assert "DagsterUnmetExecutorRequirementsError" in add_result.output


def test_tags_pipeline():
    runner = CliRunner()
    with instance_for_test() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                "-m",
                "dagster_tests.cli_tests.command_tests.test_cli_commands",
                "-a",
                "bar",
                "--tags",
                '{ "foo": "bar" }',
                "-p",
                "foo",
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
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--preset",
                "add",
                "--tags",
                '{ "foo": "bar" }',
                "-p",
                "multi_mode_with_resources",  # pipeline name
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert len(run.tags) == 1
        assert run.tags.get("foo") == "bar"


def test_execute_subset_pipeline_single_clause_solid_name():
    runner = CliRunner()
    with instance_for_test() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "foo_pipeline",
                "--solid-selection",
                "do_something",
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ["do_something"]
        assert run.solids_to_execute == {"do_something"}


def test_execute_subset_pipeline_single_clause_dsl():
    runner = CliRunner()
    with instance_for_test() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "foo_pipeline",
                "--solid-selection",
                "*do_something+",
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.solid_selection == ["*do_something+"]
        assert run.solids_to_execute == {"do_something", "do_input"}


def test_execute_subset_pipeline_multiple_clauses_dsl_and_solid_name():
    runner = CliRunner()
    with instance_for_test() as instance:
        result = runner.invoke(
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "foo_pipeline",
                "--solid-selection",
                "*do_something+,do_input",
            ],
        )
        assert result.exit_code == 0
        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert set(run.solid_selection) == set(["*do_something+", "do_input"])
        assert run.solids_to_execute == {"do_something", "do_input"}


def test_execute_subset_pipeline_invalid():
    runner = CliRunner()
    with instance_for_test():
        result = runner.invoke(
            pipeline_execute_command,
            [
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "foo_pipeline",
                "--solid-selection",
                "a, b",
            ],
        )
        assert result.exit_code == 1
        assert "No qualified solids to execute found for solid_selection" in str(result.exception)


def test_empty_working_directory():
    runner = CliRunner()

    with instance_for_test() as instance:
        with new_cwd(os.path.dirname(__file__)):
            result = runner.invoke(
                pipeline_execute_command,
                [
                    "-f",
                    file_relative_path(__file__, "file_with_local_import.py"),
                    "-a",
                    "foo_pipeline",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
