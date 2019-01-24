import subprocess
import os
import pytest
from dagster.utils import script_relative_path
from dagstermill.cli import execute_create_notebook

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
    ]
    }}
    ],
    "metadata": {{
    "celltoolbar": "Tags"
    }},
    "nbformat": 4,
    "nbformat_minor": 2
    }}'''
EXPECTED_IMPORT_STATEMENT = "from dagstermill.examples.repository import define_example_repository"


def check_notebook_expected_output(notebook_name, expected_output):
    with open(
        os.path.join(
            script_relative_path('.'),
            'notebooks',
            notebook_name if notebook_name.endswith(".ipynb") else notebook_name + ".ipynb",
        ),
        'r',
    ) as f:
        notebook_content = f.read()
        assert notebook_content == expected_output


def cleanup(notebook_name):
    notebook_path = os.path.join(
        script_relative_path("."),
        'notebooks',
        notebook_name if notebook_name.endswith(".ipynb") else notebook_name + ".ipynb",
    )
    if os.path.exists(notebook_path):
        os.remove(notebook_path)


def execute_dagstermill_cli(
    file_name=None, module_name=None, fn_name=None, notebook_name=None, solid_name=None
):
    cli_cmd = ['dagstermill', "create-notebook"]
    if file_name:
        cli_cmd += ['-f', file_name]
    if module_name:
        cli_cmd += ['--module-name', module_name]
    if fn_name:
        cli_cmd += ['--fn-name', fn_name]
    if notebook_name:
        cli_cmd += ['--notebook', notebook_name]
    if solid_name:
        cli_cmd += ['-s', solid_name]
    cli_cmd.append('--force-overwrite')

    try:
        subprocess.check_output(cli_cmd)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        raise cpe


def test_module_example():
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_dagstermill_cli(
            module_name="module_name",
            fn_name="function_name",
            notebook_name="notebooks/CLI_test_module",
            solid_name="notebook_solid",
        )
        EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
            import_statement="from module_name import function_name",
            declaration_statement="dm.declare_as_solid(function_name(), 'notebook_solid')",
        )
        check_notebook_expected_output(
            notebook_name="CLI_test_module", expected_output=EXPECTED_OUTPUT
        )
    finally:
        cleanup("CLI_test_module")
        os.chdir(original_cwd)


def test_file_example():
    with pytest.raises(subprocess.CalledProcessError) as cpe:
        execute_dagstermill_cli(
            file_name="random_file.py",
            fn_name="function_name",
            notebook_name="notebooks/CLI_test_file",
        )
        assert (
            "Cannot instantiate notebook with repository definition given by a function from a file"
            in str(cpe.value)
        )


def test_default_solid_name():
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_dagstermill_cli(
            module_name="module_name",
            fn_name="function_name",
            notebook_name="notebooks/CLI_test_default_solid",
        )
        EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
            import_statement="from module_name import function_name",
            declaration_statement="dm.declare_as_solid(function_name(), 'CLI_test_default_solid')",
        )
        check_notebook_expected_output(
            notebook_name="CLI_test_default_solid", expected_output=EXPECTED_OUTPUT
        )
    finally:
        cleanup("CLI_test_default_solid")
        os.chdir(original_cwd)


def test_yaml_example():
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_dagstermill_cli(
            notebook_name="notebooks/CLI_test_YAML", solid_name="notebook_solid"
        )
        EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
            import_statement=EXPECTED_IMPORT_STATEMENT,
            declaration_statement="dm.declare_as_solid(define_example_repository(), 'notebook_solid')",
        )
        check_notebook_expected_output(
            notebook_name="CLI_test_YAML", expected_output=EXPECTED_OUTPUT
        )
    finally:
        cleanup("CLI_test_YAML")
        os.chdir(original_cwd)


def test_invalid_filename_example():
    with pytest.raises(subprocess.CalledProcessError) as cpe:
        execute_dagstermill_cli(
            module_name="module_name",
            fn_name="function_name",
            notebook_name="notebooks/CLI!!~@",
            solid_name="notebook_solid",
        )
        assert (
            'Notebook name {name} is not valid, '
            'cannot contain anything except alphanumeric characters, '
            '-, _, \\ and / for path manipulation'
        ).format(name="CLI!!~@") in str(cpe.value)


def test_coverage():
    # tests covarage by calling scaffold from cli.py directly
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_create_notebook(
            notebook="notebooks/CLI_coverage",
            solid_name="solid_name",
            force_overwrite=True,
            module_name=None,
            fn_name=None,
            python_file=None,
            repository_yaml=None,
        )
    finally:
        cleanup("CLI_coverage")
        os.chdir(original_cwd)
