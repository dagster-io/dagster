from __future__ import print_function

import pytest

from dagster.cli.pipeline import (
    execute_print_command,
    execute_list_command,
    execute_execute_command,
)
from dagster.cli.dynamic_loader import InvalidRepositoryLoadingComboError

from dagster.utils import script_relative_path


def no_print(_):
    return None


def test_list_command():
    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        no_print,
    )

    execute_list_command(
        {
            'repository_yaml': None,
            'python_file': None,
            'module_name': 'dagster.cli.cli_tests.test_dynamic_loader',
            'fn_name': 'define_bar_repo',
        },
        no_print,
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

    with pytest.raises(InvalidRepositoryLoadingComboError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': 'foo.py',
                'module_name': 'dagster.cli.cli_tests.test_dynamic_loader',
                'fn_name': 'define_bar_repo',
            },
            no_print,
        )

    with pytest.raises(InvalidRepositoryLoadingComboError):
        execute_list_command(
            {
                'repository_yaml': None,
                'python_file': None,
                'module_name': 'dagster.cli.cli_tests.test_dynamic_loader',
                'fn_name': None,
            },
            no_print,
        )

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


def valid_cli_args():
    return [
        {
            'repository_yaml': script_relative_path('repository_file.yml'),
            'pipeline_name': ('foo', ),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': script_relative_path('repository_module.yml'),
            'pipeline_name': ('foo', ),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('foo', ),
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_bar_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': ('foo', ),
            'python_file': None,
            'module_name': 'dagster.cli.cli_tests.test_dynamic_loader',
            'fn_name': 'define_bar_repo',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': None,
            'module_name': 'dagster.cli.cli_tests.test_dynamic_loader',
            'fn_name': 'define_foo_pipeline',
        },
        {
            'repository_yaml': None,
            'pipeline_name': (),
            'python_file': script_relative_path('test_dynamic_loader.py'),
            'module_name': None,
            'fn_name': 'define_foo_pipeline',
        },
    ]


def test_print_command():
    for cli_args in valid_cli_args():
        execute_print_command(
            verbose=True,
            cli_args=cli_args,
            print_fn=no_print,
        )

    for cli_args in valid_cli_args():
        execute_print_command(
            verbose=False,
            cli_args=cli_args,
            print_fn=no_print,
        )


def test_execute_command():
    for cli_args in valid_cli_args():
        execute_execute_command(
            env=None,
            cli_args=cli_args,
            print_fn=print,
        )

    for cli_args in valid_cli_args():
        execute_execute_command(
            env=script_relative_path('env.yml'),
            cli_args=cli_args,
            print_fn=print,
        )
