from __future__ import print_function

import os

import pytest

from click.testing import CliRunner

from dagster import lambda_solid, RepositoryDefinition, pipeline, DagsterInvariantViolationError
from dagster.core.storage.runs import base_runs_directory
from dagster.cli.load_handle import CliUsageError
from dagster.cli.pipeline import (
    execute_print_command,
    execute_list_command,
    execute_execute_command,
    execute_scaffold_command,
    pipeline_execute_command,
    pipeline_list_command,
    pipeline_print_command,
    pipeline_scaffold_command,
)
from dagster.utils import script_relative_path


def no_print(_):
    return None


@lambda_solid
def do_something():
    return 1


@pipeline(name='foo')
def foo_pipeline():
    do_something()


def define_foo_pipeline():
    return foo_pipeline


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_bar_repo'],
    )
    assert result.exit_code == 0
    assert result.output == (
        'Repository bar\n'
        '**************\n'
        'Pipeline: foo\n'
        'Solids: (Execution Order)\n'
        '    do_something\n'
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-m', 'dagster_examples.intro_tutorial.repos', '-n', 'define_repo']
    )
    assert result.exit_code == 0
    assert result.output == (
        'Repository demo_repository\n'
        '**************************\n'
        'Pipeline: repo_demo_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_world\n'
    )

    execute_list_command(
        {
            'repository_yaml': script_relative_path('repository.yaml'),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        no_print,
    )

    result = runner.invoke(pipeline_list_command, ['-y', script_relative_path('repository.yaml')])
    assert result.exit_code == 0
    assert result.output == (
        'Repository demo_repository\n'
        '**************************\n'
        'Pipeline: repo_demo_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_world\n'
    )

    with pytest.raises(CliUsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster_examples.intro_tutorial.repos',
                'fn_name': 'define_repo',
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', 'foo.py', '-m', 'dagster_examples.intro_tutorial.repos', '-n', 'define_repo'],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, CliUsageError)

    with pytest.raises(CliUsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': None,
                'module_name': 'dagster_examples.intro_tutorial.repos',
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(pipeline_list_command, ['-m', 'dagster_examples.intro_tutorial.repos'])
    assert result.exit_code == 1
    assert isinstance(result.exception, CliUsageError)

    with pytest.raises(CliUsageError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command, ['-f', script_relative_path('test_cli_commands.py')]
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, CliUsageError)


def valid_execute_args():
    return [
        {
            'repository_yaml': script_relative_path('repository_file.yaml'),
            'pipeline_name': ('foo',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': script_relative_path('repository_module.yaml'),
            'pipeline_name': ('repo_demo_pipeline',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('foo',),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('repo_demo_pipeline',),
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': None,
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'fn_name': 'repo_demo_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'define_foo_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_cli_commands.py'),
            'module_name': None,
            'fn_name': 'foo_pipeline',
        },
    ]


def valid_cli_args():
    return [
        ['-y', script_relative_path('repository_file.yaml'), 'foo'],
        ['-y', script_relative_path('repository_module.yaml'), 'repo_demo_pipeline'],
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_bar_repo', 'foo'],
        ['-m', 'dagster_examples.intro_tutorial.repos', '-n', 'define_repo', 'repo_demo_pipeline'],
        ['-m', 'dagster_examples.intro_tutorial.repos', '-n', 'repo_demo_pipeline'],
        ['-f', script_relative_path('test_cli_commands.py'), '-n', 'define_foo_pipeline'],
    ]


def test_print_command():
    for cli_args in valid_execute_args():
        execute_print_command(verbose=True, cli_args=cli_args, print_fn=no_print)

    for cli_args in valid_execute_args():
        execute_print_command(verbose=False, cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_print_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_print_command, ['--verbose'] + cli_args)
        assert result.exit_code == 0


def test_execute_mode_command():
    runner = CliRunner()

    add_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path('../environments/multi_mode_with_resources/add_mode.yaml'),
            '-d',
            'add_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert add_result

    mult_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path('../environments/multi_mode_with_resources/mult_mode.yaml'),
            '-d',
            'mult_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert mult_result

    double_adder_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '--env',
            script_relative_path(
                '../environments/multi_mode_with_resources/double_adder_mode.yaml'
            ),
            '-d',
            'double_adder_mode',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert double_adder_result


def test_execute_preset_command():
    runner = CliRunner()
    add_result = runner_pipeline_execute(
        runner,
        [
            '-y',
            script_relative_path('../repository.yaml'),
            '-p',
            'add',
            'multi_mode_with_resources',  # pipeline name
        ],
    )

    assert add_result.stdout


def test_execute_command():
    for cli_args in valid_execute_args():
        execute_execute_command(env=None, raise_on_error=True, cli_args=cli_args)

    for cli_args in valid_execute_args():
        execute_execute_command(
            env=[script_relative_path('default_log_error_env.yaml')],
            raise_on_error=True,
            cli_args=cli_args,
        )

    runner = CliRunner()

    for cli_args in valid_cli_args():
        runner_pipeline_execute(runner, cli_args)

        runner_pipeline_execute(
            runner, ['--env', script_relative_path('default_log_error_env.yaml')] + cli_args
        )


def test_fn_not_found_execute():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env=None,
            raise_on_error=True,
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'nope',
            },
        )

    assert 'nope not found in module' in str(exc_info.value)


def not_a_repo_or_pipeline_fn():
    return 'kdjfkjdf'


not_a_repo_or_pipeline = 123


def test_fn_is_wrong_thing():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env=None,
            raise_on_error=True,
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'not_a_repo_or_pipeline',
            },
        )

    assert str(exc_info.value) == (
        'not_a_repo_or_pipeline must be a function that returns a '
        'PipelineDefinition or a RepositoryDefinition, or a function '
        'decorated with @pipeline.'
    )


def test_fn_returns_wrong_thing():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_execute_command(
            env=None,
            raise_on_error=True,
            cli_args={
                'repository_yaml': None,
                'pipeline_name': (),
                'python_file': script_relative_path('test_cli_commands.py'),
                'module_name': None,
                'fn_name': 'not_a_repo_or_pipeline_fn',
            },
        )

    assert str(exc_info.value) == (
        'not_a_repo_or_pipeline_fn is a function but must return a '
        'PipelineDefinition or a RepositoryDefinition, or be decorated '
        'with @pipeline.'
    )


def runner_pipeline_execute(runner, cli_args):
    result = runner.invoke(pipeline_execute_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                'dagster pipeline execute commands with cli_args {cli_args} '
                'returned exit_code {exit_code} with stdout:\n"{stdout}" and '
                '\nresult as string: "{result}"'
            ).format(
                cli_args=cli_args, exit_code=result.exit_code, stdout=result.stdout, result=result
            )
        )
    return result


def test_scaffold_command():
    for cli_args in valid_execute_args():
        cli_args['print_only_required'] = True
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

        cli_args['print_only_required'] = False
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_scaffold_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_scaffold_command, ['-p'] + cli_args)
        assert result.exit_code == 0


def test_default_memory_run_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(env=None, raise_on_error=True, cli_args=cli_args)
    assert result.success

    run_dir = os.path.join(base_runs_directory(), result.run_id)

    assert not os.path.isdir(run_dir)


def test_override_with_in_memory_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('in_memory_env.yaml')], raise_on_error=True, cli_args=cli_args
    )
    assert result.success

    run_dir = os.path.join(base_runs_directory(), result.run_id)

    assert not os.path.exists(run_dir)


def test_override_with_filesystem_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yaml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('filesystem_env.yaml')], raise_on_error=True, cli_args=cli_args
    )
    assert result.success

    run_dir = os.path.join(base_runs_directory(), result.run_id)

    assert os.path.exists(run_dir)
