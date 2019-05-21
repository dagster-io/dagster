# encoding: utf-8

import contextlib
import json
import os
import sys

import pytest

from click.testing import CliRunner

from dagster.utils import pushd, script_relative_path
from dagstermill.cli import create_notebook, retroactively_scaffold_notebook

EXPECTED_OUTPUT_SHELL = '''
    {{
    "cells": [
    {{
    "cell_type": "code",
    "execution_count": null,
    "metadata": {{}},
    "outputs": [],
    "source": [
        "import dagstermill as dm\\n",
        "{import_statement}\\n",
        "{declaration_statement}"
    ]
    }},
    {{
    "cell_type": "code",
    "execution_count": null,
    "metadata": {{
        "tags": [
        "parameters"
        ]
    }},
    "outputs": [],
    "source": [
        "context = dm.get_context()"
    ]
    }}
    ],
    "metadata": {{
    "celltoolbar": "Tags"
    }},
    "nbformat": 4,
    "nbformat_minor": 2
    }}'''

EXPECTED_IMPORT_STATEMENT = 'from dagstermill.examples.repository import define_example_repository'


def check_notebook_expected_output(notebook_path, expected_output):
    with open(notebook_path, 'r') as f:
        notebook_content = f.read()
        assert notebook_content == expected_output, notebook_content + '\n\n\n\n' + expected_output


@contextlib.contextmanager
def scaffold(file_name=None, module_name=None, fn_name=None, notebook_name=None):
    runner = CliRunner()
    args_ = (
        []
        + (['-f', file_name] if file_name else [])
        + (['--module-name', module_name] if module_name else [])
        + (['--fn-name', fn_name] if fn_name else [])
        + (['--notebook', notebook_name] if notebook_name else [])
        + ['--force-overwrite']
    )

    res = runner.invoke(create_notebook, args_)
    if res.exception:
        raise res.exception
    assert res.exit_code == 0

    yield os.path.abspath(notebook_name)

    if os.path.exists(notebook_name):
        os.unlink(notebook_name)


def test_module_example():
    with pushd(script_relative_path('.')):
        with scaffold(
            module_name='dagster',
            fn_name='function_name',
            notebook_name='notebooks/CLI_test_module',
        ) as notebook_path:
            EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
                import_statement='from dagster import function_name',
                declaration_statement='dm.register_repository(function_name())',
            )
            check_notebook_expected_output(
                notebook_path + '.ipynb', expected_output=EXPECTED_OUTPUT
            )


def test_yaml_example():
    with pushd(script_relative_path('.')):
        with scaffold(notebook_name='notebooks/CLI_test_YAML') as notebook_path:
            EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
                import_statement=EXPECTED_IMPORT_STATEMENT,
                declaration_statement='dm.register_repository(define_example_repository())',
            )
            check_notebook_expected_output(
                notebook_path + '.ipynb', expected_output=EXPECTED_OUTPUT
            )


def test_invalid_filename_example():
    if sys.version_info > (3,):
        with scaffold(notebook_name='notebooks/CLI!!~@您好') as _notebook_name:
            assert True
    else:
        with scaffold(notebook_name='notebooks/CLI!! ~@') as _notebook_name:
            assert True


def test_no_register_repo_info():
    with scaffold(notebook_name='foo_bar') as _notebook_name:
        assert True


def test_instantiate_from_missing_file():
    with pytest.raises(SystemExit) as exc:
        with scaffold(
            notebook_name='foo_bar', file_name='random_file.py', fn_name='function_name'
        ) as _notebook_name:
            assert True
    assert exc.value.code == 2


def test_instantiate_from_file():
    with open(script_relative_path('random_file.py'), 'w') as fd:
        fd.write('print(\'Hello, world!\')')
    try:
        with pytest.raises(SystemExit) as exc:
            with scaffold(
                notebook_name='foo_bar',
                file_name=script_relative_path('random_file.py'),
                fn_name='function_name',
            ) as _notebook_name:
                assert True
        assert exc.value.code == 2
    finally:
        os.unlink(script_relative_path('random_file.py'))


def test_retroactive_scaffold():
    notebook_path = script_relative_path('notebooks/retroactive.ipynb')
    with open(notebook_path, 'r') as fd:
        retroactive_notebook = fd.read()
    try:
        runner = CliRunner()
        args = [
            '--notebook',
            notebook_path,
            '--module-name',
            'dagstermill.examples',
            '--fn-name',
            'define_example_repository',
        ]
        runner.invoke(retroactively_scaffold_notebook, args)
        with open(notebook_path, 'r') as fd:
            scaffolded = json.loads(fd.read())
            assert [
                x
                for x in scaffolded['cells']
                if 'injected-repo-registration' in x.get('metadata', {}).get('tags', [])
            ]
    finally:
        with open(notebook_path, 'w') as fd:
            fd.write(retroactive_notebook)


def test_double_scaffold():
    notebook_path = script_relative_path('notebooks/overwrite.ipynb')
    with open(notebook_path, 'w') as fd:
        fd.write('print(\'Hello, world!\')')

    runner = CliRunner()
    args = ['--notebook', notebook_path]

    res = runner.invoke(create_notebook, args)

    assert isinstance(res.exception, SystemExit)
    assert res.exception.code == 1
    assert 'already exists and continuing will overwrite the existing notebook.' in res.output
