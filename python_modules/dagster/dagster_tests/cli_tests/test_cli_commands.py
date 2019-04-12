from __future__ import print_function

import os

import pytest

from click.testing import CliRunner

from dagster.core.runs import base_run_directory
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
from dagster.cli.dynamic_loader import InvalidRepositoryLoadingComboError

from dagster.utils import script_relative_path


def no_print(_):
    return None


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', script_relative_path('test_dynamic_loader.py'), '-n', 'define_bar_repo'],
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
            'module_name': 'dagster.tutorials.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-m', 'dagster.tutorials.intro_tutorial.repos', '-n', 'define_repo']
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
            'repository_yaml': script_relative_path('repository.yml'),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        no_print,
    )

    result = runner.invoke(pipeline_list_command, ['-y', script_relative_path('repository.yml')])
    assert result.exit_code == 0
    assert result.output == (
        'Repository demo_repository\n'
        '**************************\n'
        'Pipeline: repo_demo_pipeline\n'
        'Solids: (Execution Order)\n'
        '    hello_world\n'
    )

    with pytest.raises(InvalidRepositoryLoadingComboError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster.tutorials.intro_tutorial.repos',
                'fn_name': 'define_repo',
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command,
        ['-f', 'foo.py', '-m', 'dagster.tutorials.intro_tutorial.repos', '-n', 'define_repo'],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, InvalidRepositoryLoadingComboError)

    with pytest.raises(InvalidRepositoryLoadingComboError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': None,
                'module_name': 'dagster.tutorials.intro_tutorial.repos',
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(pipeline_list_command, ['-m', 'dagster.tutorials.intro_tutorial.repos'])
    assert result.exit_code == 1
    assert isinstance(result.exception, InvalidRepositoryLoadingComboError)

    with pytest.raises(InvalidRepositoryLoadingComboError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': script_relative_path('test_dynamic_loader.py'),
                'module_name': None,
                'fn_name': None,
            },
            no_print,
        )

    result = runner.invoke(
        pipeline_list_command, ['-f', script_relative_path('test_dynamic_loader.py')]
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, InvalidRepositoryLoadingComboError)


def valid_execute_args():
    return [
        {
            'repository_yaml': script_relative_path('repository_file.yml'),
            'pipeline_name': ('foo',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': script_relative_path('repository_module.yml'),
            'pipeline_name': ('repo_demo_pipeline',),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('foo',),
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('repo_demo_pipeline',),
            'python_file': None,
            'module_name': 'dagster.tutorials.intro_tutorial.repos',
            'fn_name': 'define_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': None,
            'module_name': 'dagster.tutorials.intro_tutorial.repos',
            'fn_name': 'define_repo_demo_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_foo_pipeline',
        },
    ]


def valid_cli_args():
    return [
        ['-y', script_relative_path('repository_file.yml'), 'foo'],
        ['-y', script_relative_path('repository_module.yml'), 'repo_demo_pipeline'],
        ['-f', script_relative_path('test_dynamic_loader.py'), '-n', 'define_bar_repo', 'foo'],
        ['-m', 'dagster.tutorials.intro_tutorial.repos', '-n', 'define_repo', 'repo_demo_pipeline'],
        ['-m', 'dagster.tutorials.intro_tutorial.repos', '-n', 'define_repo_demo_pipeline'],
        ['-f', script_relative_path('test_dynamic_loader.py'), '-n', 'define_foo_pipeline'],
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


def test_execute_command():
    for cli_args in valid_execute_args():
        execute_execute_command(env=None, raise_on_error=True, cli_args=cli_args)

    for cli_args in valid_execute_args():
        execute_execute_command(
            env=[script_relative_path('env.yml')], raise_on_error=True, cli_args=cli_args
        )

    runner = CliRunner()

    for cli_args in valid_cli_args():
        result = runner.invoke(pipeline_execute_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(
            pipeline_execute_command, ['--env', script_relative_path('env.yml')] + cli_args
        )
        assert result.exit_code == 0


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
        'repository_yaml': script_relative_path('repository_file.yml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(env=None, raise_on_error=True, cli_args=cli_args)
    assert result.success

    run_dir = os.path.join(base_run_directory(), result.run_id)

    assert not os.path.isdir(run_dir)


def test_override_with_in_memory_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('in_memory_env.yml')], raise_on_error=True, cli_args=cli_args
    )
    assert result.success

    run_dir = os.path.join(base_run_directory(), result.run_id)

    assert not os.path.exists(run_dir)


def test_override_with_filesystem_storage():
    cli_args = {
        'repository_yaml': script_relative_path('repository_file.yml'),
        'pipeline_name': ('foo',),
        'python_file': None,
        'module_name': None,
        'fn_name': None,
    }
    result = execute_execute_command(
        env=[script_relative_path('filesystem_env.yml')], raise_on_error=True, cli_args=cli_args
    )
    assert result.success

    run_dir = os.path.join(base_run_directory(), result.run_id)

    assert os.path.exists(run_dir)
